from flask import Flask
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource
import csv
import random
import time
import requests

app = Flask(__name__)
api = Api(app)

ORDER_FILE = 'order_log.txt'
SERVER_CONFIG = 'server_config'

PERIODIC_UPDATE = False

#######################################################
############### Accessing Catalog server  #############
#######################################################

with open(SERVER_CONFIG, mode ='r') as server_file:
    server_dict = {}
    csv_reader = csv.DictReader(server_file)
    for row in csv_reader:
        server_name = row['Server']
        server_dict[server_name] = {'Machine': row['Machine'],
                                    'IP': row['IP'],
                                    'Port': row['Port']}
    
    catalog_dict = server_dict['Catalog']
    catalog_IP = catalog_dict['IP']
    catalog_port = catalog_dict['Port']
    ORDER_PORT = server_dict['Order']['Port']

CATALOG_ADDRESS = 'http://' + catalog_IP + ':' + catalog_port


#######################################################
#### Helper functions for read/writing to order DB ####
#######################################################
def reset_orders():
    # initialize order database as a local .txt file
    with open(ORDER_FILE, mode='w') as order_log:
        fieldnames = ['order_id', 'processing_time','is_successful','catalog_id','title']
        writer = csv.DictWriter(order_log, fieldnames=fieldnames)
        writer.writeheader()

def get_orders_as_dict():
    with open(ORDER_FILE, mode='r') as csv_file:
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

def write_order(order):
    with open(ORDER_FILE, mode='a') as order_log:
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
    r = requests.get(CATALOG_ADDRESS + '/query/' + catalog_id)
    query_result = r.json()
    # querying by ID gives a json of type {title:{'COST':value, 'QUANTITY':value}}
    title = list(query_result.keys())[0]
    item_dict = list(query_result.values())[0]
    quantity = int(item_dict['QUANTITY'])

    return quantity,title

# decrements the catalog server, returns the new quantity 
def decrement_catalog_server(catalog_id):
    r = requests.get(CATALOG_ADDRESS + '/update/' + catalog_id + '/quantity/decrease/1')
    decrement_result = r.json()
    # updating by quantity gives a json of type {title:{'COST':value, 'QUANTITY':value}}
    item_dict = list(decrement_result.values())[0]
    quantity = int(item_dict['QUANTITY'])
    cost = int(item_dict['COST'])

    return quantity

def restock_catalog_server(catalog_id):
    r = requests.get(CATALOG_ADDRESS + '/update/' + catalog_id + '/quantity/increase/300')



######################################################
################ Setup REST resources ################
######################################################

# Buy
# submit a single buy request

class Buy(Resource):
    order = {}
    def get(self, catalog_id):
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
                title = title + errorString
        order = create_order(order_id,processing_time,is_successful,catalog_id,title)
        write_order(order)
        return jsonify(order)




# OrderList
# shows a list of all orders
class OrderList(Resource):
    def get(self):
        orders = get_orders_as_dict()
        return jsonify(orders)
    
    def delete(self):
        reset_orders()
        orders = get_orders_as_dict()
        return jsonify(orders)

##
## setup the Api resource routing here
##
api.add_resource(OrderList, '/orders')
api.add_resource(Buy, '/buy/<catalog_id>')


if __name__ == '__main__':
    # reset the order DB when starting the flask app
    reset_orders()
    app.run(host = '0.0.0.0', port = ORDER_PORT)

