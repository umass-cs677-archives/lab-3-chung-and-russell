from flask import Flask, jsonify, abort, g, request, Response, make_response
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
import codecs

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
    try:
        r = requests.get(app.config.get("catalog_address") + 'query/' + catalog_id)
        query_result = r.json()
        # querying by ID gives a json of type {title:{'COST':value, 'QUANTITY':value}}
        title = list(query_result.keys())[0]
        item_dict = list(query_result.values())[0]
        quantity = int(item_dict['QUANTITY'])
        return quantity,title
    except requests.exceptions.ConnectionError:
        # server must have been down, change my catalog address
        print("Catalog server replica down, trying another one")
        catalog_id = app.config.get("catalog_name").split("_")[1]
        if catalog_id == '0':
            new_id = '1'
        else:
            new_id = '0'
        app.config["catalog_name"] = "Catalog_" + new_id
        app.config["catalog_address"] = get_root_url(server_dict,app.config["catalog_name"])
        return query_catalog_server(catalog_id)

        


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


def hold_election(id = None):
    """
    Set self to primary
    """
    primary_id = app.config.get("id")

    # Current server is primary.  No need to notify others, since they must be down
    app.config["primary"] = app.config.get("name")
    print(app.config.get("name") + "is now the primary")
    return Response(app.config.get("name") + " won", status=200)

def notify_all():
    # Propogate this server's primary to all other servers
    server_dict = app.config.get("server_dict")
    for server_name, _ in server_dict.items():
        if "Order" in server_name and server_name != app.config.get("name"):
            root_url = get_root_url(app.config.get("server_dict"), server_name)
            query = string_builder([root_url], "notify/", app.config.get("primary"))
            try:
                # Make a notify request
                requests.get(query)
            except requests.exceptions.ConnectionError:
                # server must have been down
                print("Failed to notify ", server_name, " the election result.")

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
        print("primary server down, I am now the primary")
        # Current server is primary.  No need to notify others, since they must be down
        app.config["primary"] = app.config.get("name")
        # Retry the request
        return forward(query, app.config.get("primary"))


def sync_up(server_dict, peer_name_ids):
    """
    sync up with the first available server (which must be the primary)
    """
    for peer_name_id in peer_name_ids:
        if peer_name_id[0] != app.config.get("name"):
            peer_root_url = get_root_url(server_dict, peer_name_id[0])
            try:
                download_query = string_builder([peer_root_url], "download/", "order_",  peer_name_id[1], "_db.txt")
                r = requests.get(download_query)
                target_db = string_builder(["order_"], app.config["id"], "_db.txt")
                with open(target_db, "wb") as db:
                    db.write(r.content)
                print(app.config.get("name"),string_builder([], "sync up with replica", peer_name_id[1]))
                return
            except requests.exceptions.ConnectionError:
                print(peer_name_id[0], " not running")
    print("No other running servers, " + app.config.get("name") +" is resetting")
    reset_orders()

def db_check():
    server_dict = app.config.get("server_dict")
    peer_name_ids = list(get_replicas(server_dict, "Order"))
    for peer_name_id in peer_name_ids:
        if peer_name_id[0] != app.config.get("name"):
            peer_root_url = get_root_url(server_dict, peer_name_id[0])
            try:
                # download db of peer
                download_query = string_builder([peer_root_url], "download/", "order_",  peer_name_id[1], "_db.txt")
                r = requests.get(download_query)
                peer_db = r.content
                # download own db
                own_filename = string_builder(["order_"], app.config["id"], "_db.txt")
                file_data = codecs.open(own_filename, 'rb').read()
                #response = make_response()
                #response.data = file_data
                own_db = file_data
                print(type(own_db))
                print(type(peer_db))
                
                if own_db == peer_db:
                    return "Database synced with peer!"
                else:
                    return "Database not synced."
            except requests.exceptions.ConnectionError:
                print(peer_name_id[0], " not running")
    return "No other running servers to check with"


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



def startup_config():
    app.config["id"] = sys.argv[1]
    app.config["name"] = "Order_" + app.config["id"]
    app.config["order_db"] = "order_" + app.config["id"] + "_db.txt"
    app.config["server_dict"] = get_server_dict("server_config", ["Client"])
    # Redundant variable assignment make the calls to this reference shorter
    server_dict = app.config["server_dict"]

    # save peer id and names
    replica_names, replica_ids = zip(*get_replicas(server_dict, "Order"))
    app.config["peer_ids"] = list(replica_ids)
    app.config["peer_names"] = list(replica_names)

    app.config["order_ip"], app.config["order_port"] = get_id_port(server_dict, "Order", app.config.get("id"))
    app.config["catalog_name"] = "Catalog_" + app.config["id"]
    app.config["catalog_address"] = get_root_url(server_dict,app.config["catalog_name"])

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


class Download(Resource):
    def get(self,filename):
        file_data = codecs.open(filename, 'rb').read()
        response = make_response()
        response.data = file_data
        return response

class DBCheck(Resource):
    def get(self):
        return db_check()




##
## setup the Api resource routing here
##
api.add_resource(OrderList, '/orders')
api.add_resource(Buy, '/buy/<catalog_id>')
api.add_resource(Write, '/write/<order_id>/<processing_time>/<is_successful>/<catalog_id>/<title>')
api.add_resource(Notify, '/notify/<primary_name>')
api.add_resource(Download, '/download/<filename>')
api.add_resource(DBCheck,'/check')


if __name__ == '__main__':
    startup_config()
    # Assume primary is Order_0 on startup, notify others
    app.config["primary"] = "Order_0"
    notify_all()

    server_dict = app.config.get("server_dict")
    sync_up(server_dict, list(get_replicas(server_dict, "Order")))
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(app.run, host=app.config.get("order_ip"), port=app.config.get("order_port"))

