from flask import Flask
import requests
import csv
import random
from src.utils import string_builder

app = Flask("frontend")

SERVER_CONFIG = 'server_config'

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
    
#     CATALOG_PORT = server_dict['Catalog']['Port']
#     ORDER_PORT = server_dict['Order']['Port']
#     FRONTEND_PORT = server_dict['Frontend']['Port']
#
#
# CATALOG_QUERY = 'http://128.119.243.164:' + CATALOG_PORT + '/query/'
# ORDER_BUY = 'http://128.119.243.147:' + ORDER_PORT + '/buy/'

N_SERVER_REPLICAS = 2
cache = {}


def get_server_location(server_type : str) -> str:
    """
    Load balancing between replicas

    :param server_type: type of the server. Either CATALOG or ORDER
    :return: The location of one of the replicas for the specified server type
    """
    # The idea is that picking a random replica will even out the loading
    # on all replicas in long term
    replica_n = random.randint(0, N_SERVER_REPLICAS - 1)
    server_location = ["http://"]
    server_name = server_type + "_" + str(replica_n)
    server_ip = server_dict[server_name]["IP"]
    server_port = server_dict[server_name]["Port"]
    string_builder(server_location, server_ip, ":", server_port, "/")

    return "".join(server_location)


@app.route("/invalidate/<entry_key>")
def invalidate(entry_key):
    """
    Delete specify entry from the cache. It could be a topic name or an item number
    """
    del cache[entry_key]


@app.route("/search/<topic>", methods=["GET"])
def search(topic: str) -> str:
    if topic in cache:
        return cache[topic]

    catalog_server_location = get_server_location("Catalog")
    books = requests.get(catalog_server_location + topic).json()

    search_result = []

    for book in books["items"]:
        search_result.append("Name: ")
        search_result.append(book)
        search_result.append(" Item ID: ")
        search_result.append(str(books["items"][book]))
        search_result.append("\n")

    result = "".join(search_result)
    cache[topic] = result

    return "".join(search_result)


# @app.route("/lookup/<item_number>")
# def lookup(item_number):
#     books = requests.get(CATALOG_QUERY + item_number).json()
#
#     search_result = []
#
#     for book in books:
#         search_result.append("Name: ")
#         search_result.append(book)
#         search_result.append("\n")
#         search_result.append("Cost: ")
#         search_result.append(str(books[book]["COST"]))
#         search_result.append("\n")
#         search_result.append("Quantity: ")
#         search_result.append(str(books[book]["QUANTITY"]))
#         search_result.append("\n")
#
#     return "".join(search_result)
#
#
# @app.route("/buy/<catalog_id>")
# def buy(catalog_id):
#     response = requests.get(ORDER_BUY + catalog_id).json()
#
#     if response["is_successful"]:
#         return "bought book '" + response["title"] + "'\n"
#
#     return "failed to buy book '" + response["title"] + "'\n"


if __name__ == "__main__":
    app.run(host='0.0.0.0')
