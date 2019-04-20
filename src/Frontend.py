from flask import Flask
import requests
import random
from utils import *
from typing import Set

app = Flask("frontend")
server_dict = get_server_dict("server_config")
catalog_replicas = get_replicas(server_dict, "Catalog")
cache = {}


def get_server_location(replicas: Set[str]):
    """
    Load balancing between replicas

    :param replicas: list of available replicas
    :return: The location of one of the replicas for the specified server type
    """
    # The idea is that picking a random replica will even out the loading
    # on all replicas in long term
    server_location = ["http://"]
    name = random.sample(replicas, 1)[0]
    server_ip = server_dict[name]["IP"]
    server_port = server_dict[name]["Port"]
    server_location = string_builder(server_location, server_ip, ":", server_port)

    return server_location


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

    catalog_server_location = get_server_location(catalog_replicas)
    query = string_builder([], catalog_server_location, "/query/", topic)
    books = requests.get(query).json()
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
    app.run(port=5001)
