from flask import Flask
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource
from utils import *
from concurrent.futures import ThreadPoolExecutor
import csv
import random
import time
import requests
import sys
from threading import Lock

app = Flask(__name__)
api = Api(app)

app.config["order_db"] = 'order_log.txt'
SERVER_CONFIG = 'server_config'

PERIODIC_UPDATE = False

lock = Lock()
#######################################################
#### Helper functions for read/writing to order DB ####
#######################################################
def reset_orders():
    # initialize order database as a local .txt file
    with open(app.config["order_db"], mode='w') as order_log:
        fieldnames = ['order_id', 'processing_time','is_successful','catalog_id','title']
        writer = csv.DictWriter(order_log, fieldnames=fieldnames)
        writer.writeheader()

def get_orders_as_dict():
    with open(app.config["order_db"], mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        return [row for row in csv_reader]

def get_num_orders():
    orders = get_orders_as_dict()
    return len(orders)

def create_order(order_id,processing_time,is_successful,catalog_id,title):
    return {'order_id': order_id,
            'processing_time': processing_time,
            'is_successful': is_successful,
            'catalog_id': catalog_id,
            'title': title}

def package_order_into_string(input):
    return "<ORDER_INFO>".join(input)

def unpack_string_into_order(input):
    order_id,processing_time,is_successful,catalog_id,title = input.split("<ORDER_INFO>")
    if is_successful == "True":
        is_successful = True
    else:
        is_successful = False
    return create_order(int(order_id),float(processing_time),is_successful,catalog_id,title)


def write_order(order):
    with open(app.config["order_db"], mode='a') as order_log:
        fieldnames = ['order_id', 'processing_time','is_successful','catalog_id','title']
        writer = csv.DictWriter(order_log, fieldnames=fieldnames)
        writer.writerow(order)

#######################################################
######## Functions for querying catalog server ########
#######################################################

parser = reqparse.RequestParser()
parser.add_argument('catalog_id', type = int, help = 'Catalog ID for item to buy')

# queries the catalog server, returns the quantity and title of the item
def query_catalog_server(catalog_id):
    r = requests.get(app.config.get("catalog_address") + 'query/' + catalog_id)
    query_result = r.json()
    # querying by ID gives a json of type {title:{'COST':value, 'QUANTITY':value}}
    title = list(query_result.keys())[0]
    item_dict = list(query_result.values())[0]
    quantity = int(item_dict['QUANTITY'])

    return quantity,title

# decrements the catalog server, returns the new quantity 
def decrement_catalog_server(catalog_id):
    r = requests.put(app.config.get("catalog_address") + 'update/' + catalog_id + '/quantity/decrease/1')
    decrement_result = r.json()
    # updating by quantity gives a json of type {title:{'COST':value, 'QUANTITY':value}}
    item_dict = list(decrement_result.values())[0]
    quantity = int(item_dict['QUANTITY'])
    cost = int(item_dict['COST'])

    return quantity

def restock_catalog_server(catalog_id):
    r = requests.put(app.config.get("catalog_address") + 'update/' + catalog_id + '/quantity/increase/300')

def forward(query, server_name, is_get = True):
    """
    Forward the query for the specified server to execute
    """
    root_url = get_root_url(app.config.get("server_dict"), server_name)
    forward_query = string_builder([root_url], query)
    try:
        if is_get:
            r = requests.get(forward_query)
            return r
        else:
            r = requests.put(forward_query)
            return r

    except requests.exceptions.ConnectionError:
        # Primary server is down, holds an election and forwards the
        # request to the new primary
        print("primary server down")
        #hold_election()
        return forward(query, app.config.get("primary"))

def sync_all(query):
    """
    Synchronize other non-primary servers
    """
    for peer_name in app.config.get("peer_names"):
        # No need to sync up with itself
        if peer_name != app.config.get("name"):
            root_url = get_root_url(app.config.get("server_dict"), peer_name)
            sync_query = string_builder([root_url], query)
            try:
                r = requests.post(sync_query)
            except requests.exceptions.ConnectionError:
                app.config.get("peer_names").remove(peer_name)
                print(peer_name + " is down")

######################################################
################ Setup REST resources ################
######################################################

# Buy
# submit a single buy request

class Buy(Resource):
    order = {}
    def get(self, catalog_id):
        # not the primary replica, forward request to primary
        if app.config.get("primary") != app.config.get("name") :
            #order_string = package_order_into_string([str(order_id),str(processing_time),str(is_successful),catalog_id,title])
            query = string_builder([], "buy/", catalog_id)
            r = forward(query, app.config.get("primary"))
            return r.json()
        # executed by primary replica
        else:
            with lock:
                start = time.time()
                stock,title = query_catalog_server(catalog_id)
                processing_time = time.time() - start
                if stock <= 0:
                    # done querying the catalog server, add an order to the order DB
                    order_id = get_num_orders() + 1
                    is_successful = False
                    if PERIODIC_UPDATE:
                        restock_catalog_server(catalog_id)

                else:
                    #decrement stock by 1
                    newstock = decrement_catalog_server(catalog_id)
                    is_successful = True
                    order_id = get_num_orders() + 1
                    stockChange = stock - newstock
                    if stockChange != 1:
                        if newstock < 0:
                            errorString = ", stock is now " + str(newstock)
                        else:
                            errorString = " ,  " + str(stockChange) + " other clients bought items in between query and update"
                        print("Bought '"+ title + "' , stock erroneously changed by " + str(stockChange))
                        title = title
                order = create_order(order_id,processing_time,is_successful,catalog_id,title)
                # Need to block on write until the replicas are notified
                executor = ThreadPoolExecutor(max_workers=2)
                write_order(order)
                query = string_builder([], "write/", str(order_id), "/", str(processing_time), "/", str(is_successful), "/", str(catalog_id),"/",str(title))
                executor.submit(sync_all, query)
                return jsonify(order)

class Notify(Resource):
    def get(self, primary_name):
        """
        Get notified which server is the new primary
        """
        app.config["primary"] = primary_name
        return(primary_name+ " is the new primary")
    
class Write(Resource):
    def post(self, order_id,processing_time,is_successful,catalog_id,title):
        # need to convert strings to proper formats
        is_successful = (is_successful== "True")
        order = create_order(int(order_id),float(processing_time),is_successful,int(catalog_id),title)
        write_order(order)


# OrderList
# shows a list of all orders
class OrderList(Resource):
    def get(self):
        orders = get_orders_as_dict()
        return orders
    
    def delete(self):
        reset_orders()
        # reset orders in replica
        orders = get_orders_as_dict()
        return jsonify(orders)


##
## setup the Api resource routing here
##
api.add_resource(OrderList, '/orders')
api.add_resource(Buy, '/buy/<catalog_id>')
api.add_resource(Write, '/write/<order_id>/<processing_time>/<is_successful>/<catalog_id>/<title>')
api.add_resource(Notify, '/notify/<primary_name>')


if __name__ == '__main__':

    #######################################################
    ############### Accessing Catalog server  #############
    #######################################################


    def get_address(address_dict):
        IP = address_dict['IP']
        port = address_dict['Port']
        address = 'http://' + IP + ':' + port
        return address

    with open(SERVER_CONFIG, mode ='r') as server_file:
        server_dict = {}
        csv_reader = csv.DictReader(server_file)
        for row in csv_reader:
            server_name = row['Server']
            server_dict[server_name] = {'Machine': row['Machine'],
                                        'IP': row['IP'],
                                        'Port': row['Port'],
                                        'Replica_ID': row['Replica_num']}
        
        catalog_dict_0 = server_dict['Catalog_0']
        catalog_address_0 = get_address(catalog_dict_0)
        catalog_dict_1 = server_dict['Catalog_1']
        catalog_address_1 = get_address(catalog_dict_1)
        ORDER_PORT_0 = server_dict['Order_0']['Port']
        ORDER_PORT_1 = server_dict['Order_1']['Port']
        CATALOG_ADDRESS = catalog_address_0

    # reset the order DB when starting the flask app
    
    # config variables
    app.config["id"] = sys.argv[1]
    app.config["name"] = "Order_" + app.config["id"]
    app.config["order_db"] = "order_" + app.config["id"] + "_db.txt"
    app.config["server_dict"] = get_server_dict("server_config", ["Client"])
    # Redundant variable assignment make the calls to this reference shorter
    server_dict = app.config["server_dict"]
    replica_names, replica_ids = zip(*get_replicas(server_dict, "Order"))
    app.config["peer_ids"] = list(replica_ids)
    # Assume a primary, if the assumed primary isn't in fact running, another
    # primary will be elected later on
    app.config["primary"] = "Order_" + str(max(app.config["peer_ids"]))
    app.config["peer_names"] = list(replica_names)
    order_ip, order_port = get_id_port(server_dict, "Order", app.config.get("id"))
    app.config["catalog_name"] = "Catalog_" + app.config["id"]

    catalog_ip, catalog_port = get_id_port(server_dict, "Catalog", app.config.get("id"))
    app.config["catalog_name"] = "Catalog_" + app.config["id"]
    app.config["catalog_address"] = get_root_url(server_dict,app.config["catalog_name"])

    reset_orders()
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(app.run, host=order_ip, port=order_port)

