from flask import Flask
import requests
import random
from utils import *

app = Flask("frontend")
server_dict = get_server_dict("server_config")
catalog_replicas = get_replicas(server_dict, "Catalog")
catalog_replica_names, _ = zip(*catalog_replicas)
catalog_replica_names = list(catalog_replica_names)
order_replicas = get_replicas(server_dict, "Order")
order_replica_names, _ = zip(*order_replicas)
order_replica_names = list(order_replica_names)
cache = {}


def get_server_location(replicas):
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

    return server_location, name


@app.route("/notify/<server_type>/<server_id>", methods=["PUT"])
def get_notified(server_type, server_id):
    """
    API for a server to notify frontend
    """
    if server_type == "Catalog":
        catalog_replica_names.append(string_builder([server_type],"_", server_id))
    if server_type == "Order":
        order_replica_names.append(string_builder([server_type],"_", server_id))
    return "succesfully registered with frontend"

@app.route("/invalidate/<entry_key>", methods=["PUT"])
def invalidate(entry_key):
    """
    Delete specify entry from the cache. It could be a topic name or an item number
    """
    del cache[entry_key]
    # print(string_builder([], "cache entry ",  entry_key, " invalidated"))
    return "Entry " + entry_key + " invalidated"


@app.route("/search/<topic>", methods=["GET"])
def search(topic: str) -> str:
    if topic in cache:
        print("cache hit")
        return cache[topic]

    catalog_server_location, server_name = get_server_location(catalog_replica_names)
    query = string_builder([], catalog_server_location, "/query/", topic)
    try:
        books = requests.get(query).json()
        search_result = []

        for book in books["items"]:
            search_result.append("Name: ")
            search_result.append(book)
            search_result.append(" Item ID: ")
            search_result.append(str(books["items"][book]))
            search_result.append("\n")

        search_result = "".join(search_result)
        cache[topic] = search_result

        return search_result

    except requests.exceptions.ConnectionError:
        # if server_name in catalog_replica_names:
        #     catalog_replica_names.remove(server_name)
        return search(topic)


@app.route("/lookup/<item_number>")
def lookup(item_number):
    if item_number in cache:
        print("cache hit")
        return cache[item_number]
    catalog_server_location, server_name = get_server_location(catalog_replica_names)
    query = string_builder([], catalog_server_location, "/query/", item_number)

    try:
        books = requests.get(query).json()

        search_result = []

        for book in books:
            search_result.append("Name: ")
            search_result.append(book)
            search_result.append("\n")
            search_result.append("Cost: ")
            search_result.append(str(books[book]["COST"]))
            search_result.append("\n")
            search_result.append("Quantity: ")
            search_result.append(str(books[book]["QUANTITY"]))
            search_result.append("\n")

        search_result = "".join(search_result)
        cache[item_number] = search_result
        return search_result

    except requests.exceptions.ConnectionError:
        # if server_name in catalog_replica_names:
        #     catalog_replica_names.remove(server_name)
        return lookup(item_number)
#
#
@app.route("/buy/<catalog_id>")
def buy(catalog_id):
    order_server_location, server_name = get_server_location(order_replica_names)
    query = string_builder([], order_server_location, "/buy/", catalog_id)
    try:
        response = requests.get(query).json()
        print(response)
        if response["is successful"]:
            return "bought book '" + response["title"] + "'\n"
        return "failed to buy book '" + response["title"] + "'\n"
    except requests.exceptions.ConnectionError:
        return buy(topic)


if __name__ == "__main__":
    app.config["server_dict"] = get_server_dict("server_config")
    server_dict = app.config["server_dict"]
    frontend_ip, frontend_port = get_id_port(server_dict, "Frontend")
    app.run(host="0.0.0.0", port=frontend_port)
