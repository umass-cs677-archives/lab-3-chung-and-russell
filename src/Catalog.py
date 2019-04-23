import sqlite3
import requests
from flask import Flask, jsonify, abort, g, request, Response
from utils import *
from concurrent.futures import ThreadPoolExecutor
import sys
import subprocess

app = Flask("catalog")
locks = get_locks(7)

def get_db(id):
    database = ["inventory"]
    database = string_builder(database, "_", id, ".db")
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(database)

    def make_dicts(cursor, row):
        return dict((cursor.description[idx][0], value)
                    for idx, value in enumerate(row))

    db.row_factory = make_dicts

    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def _pair_results(query_results, fields_to_pair):
    """
    It pairs up entries of the dictionaries in the query result. For example,
    two dictionaries {a : "book1", b : 10} {a : "book2", b : 25}
    will be packed into one dictionary {"book1" : 10, "book2" : 25}

    :param query_results: A list of dictionaries. All dictionaries must have the same keys or the function will fail
    :param fields_to_pair: list of tuples of string that specify what entries in a dictionary to pair up

    :return: a dictionary that has values of the paired fields as keys and values
    """

    paired_dict = {}

    for query_result in query_results:

        for pair in fields_to_pair:
            new_key = query_result[pair[0]]
            new_value = query_result[pair[1]]

            paired_dict[new_key] = new_value

    return paired_dict


def _delete_keys(dict, keys):
    """
    Delete specified keys from the dictionary
    """
    for key in keys:
        del dict[key]

    return dict


@app.route("/query/<topic>", methods=['GET'])
@app.route("/query/<int:item_number>", methods=['GET'])
def query(**kwargs):
    key = list(kwargs)[0]
    cursor = get_db(app.config.get("id")).cursor()

    if key == "topic":
        topic = (kwargs[key].replace("_", " "),)
        query_results = cursor.execute("SELECT name, id FROM books WHERE topic = ?", topic).fetchall()
        query_results = _pair_results(query_results, [("NAME", "ID")])
        response = jsonify(items=query_results)
    elif key == "item_number":

        with locks[kwargs[key] - 1]:
            query_result = cursor.execute("SELECT name, cost, quantity FROM books WHERE id = ?",
                                          str(kwargs[key])).fetchall()
            book_name = query_result[0]["NAME"]
            response = jsonify({book_name: _delete_keys(query_result[0],["NAME"])})

    else:
        return "no query criteria specified"

    return response


@app.route("/update/<item_number>/<field>/<operation>/<int:number>", methods=['PUT'])
@app.route("/sync/<item_number>/<field>/<operation>/<int:number>", methods=['PUT'])
def update(item_number, field, operation, number):
    """

    Update field using given operation and number. A successful update will automatically
    redirect to /query/item_number and displays the updated item info

    :param item_number: item to update
    :param field: name of the field to update
    :param operation: three operations are supported. increase, decrease, and set
    :param number: number to be used in operation
    :return: updated json object
    """

    valid_fields = ["cost", "quantity"]
    valid_operation = {"increase":"+", "decrease":"-", "set":""}

    # Checking fields for validation also prevents SQL injection attack,
    # so it's safe to concatenate <field> to the query
    if field not in valid_fields:
        abort(400)

    if operation not in valid_operation:
        abort(400)

    if number < 0:
        abort(400)

    # Not the primary replica, forward the request
    if app.config.get("primary") != app.config.get("name") and "sync" not in request.path:
        query = string_builder([], "update/", item_number,"/", field, "/", operation, "/", str(number))
        r = forward(query, app.config.get("primary"))
        return r

    conn = get_db(app.config.get("id"))
    cursor = conn.cursor()
    success = True

    with locks[int(item_number) - 1]:
        if operation == "increase":
            cursor.execute("UPDATE books SET " + field + "=" + field + valid_operation[operation] + " ? WHERE ID = ?",
                           [str(number), item_number])
            conn.commit()

        elif operation == "decrease":
            # Check the value again before decrement
            query_result = cursor.execute("SELECT cost, quantity FROM books WHERE id = ?", item_number).fetchall()

            if query_result[0][field.upper()] > 0:
                cursor.execute(
                    "UPDATE books SET " + field + "=" + field + valid_operation[operation] + " ? WHERE ID = ?",
                    [str(number), item_number])
                conn.commit()
            else:
                success = False

        elif operation == "set":
            cursor.execute("UPDATE books SET " + field + "= ? WHERE ID = ?", [str(number), str(item_number)])
            conn.commit()


        query_result = cursor.execute("SELECT name, cost, quantity FROM books WHERE id = ?", item_number).fetchall()
        book_name = query_result[0]["NAME"]
        query_result[0]["SUCCESS"] = success

        executor = ThreadPoolExecutor(max_workers=2)
        if app.config.get("primary") == app.config.get("name"):
            # Sync other non-primary servers
            query = string_builder([], "sync/", item_number, "/", field, "/", "set", "/", str(query_result[0][field.upper()]))
            executor.submit(sync_all, query)
            # Invalidate front end cache
            front_end_url = get_root_url(app.config.get("server_dict"), "Frontend")
            invalidate_query = string_builder([front_end_url], "invalidate/", str(item_number))
            executor.submit(requests.put, invalidate_query)

        response = jsonify({book_name: _delete_keys(query_result[0], ["NAME"])})

    return response


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
                r = requests.put(sync_query)
            except requests.exceptions.ConnectionError:
                app.config.get("peer_names").remove(peer_name)
                print(peer_name + " is down")


@app.route("/notify/<primary_name>")
def notify(primary_name):
    """
    Get notified which server is the new primary
    """
    app.config["primary"] = primary_name
    print(primary_name, " is the new primary")
    # Register itself with the new primary
    primary_root_url = get_root_url(app.config.get("server_dict"), primary_name)
    try:
        register_query = string_builder([primary_root_url], "register/", app.config.get("name"))
        requests.put(register_query)
        
    except requests.exceptions.ConnectionError:
        # Primary server is down, holds an election and forwards the
        # request to the new primary
        print("primary server down")
        hold_election()

    return "notified"


def forward(query, server_name):
    """
    Forward the query for the specified server to execute
    """
    root_url = get_root_url(app.config.get("server_dict"), server_name)
    forward_query = string_builder([root_url], query)
    try:
        r = requests.put(forward_query)
        return r.text
    except requests.exceptions.ConnectionError:
        # Primary server is down, holds an election and forwards the
        # request to the new primary
        print("primary server down")
        hold_election()
        return forward(query, app.config.get("primary"))


def get_candidates(peer_ids, self_id):
    """
    Get a list of candidates whose IDs are higher.

    :param peer_ids: list of all peer IDs
    :param self_id: ID of the server who initiates the election
    :return: suitable candidates who have higher IDs than self_id
    """
    candidates = []

    for peer_id in peer_ids:
        if peer_id > self_id:
            candidates.append(peer_id)

    return candidates


def notify_all():
    server_dict = app.config.get("server_dict")

    for server_name, _ in server_dict.items():
        if "Catalog" in server_name and server_name != app.config.get("name"):
            root_url = get_root_url(app.config.get("server_dict"), server_name)
            query = string_builder([root_url], "notify/", app.config.get("name"))
            try:
                # Make a notify request
                requests.get(query)
            except requests.exceptions.ConnectionError:
                if server_name in app.config.get("peer_names"):
                    app.config.get("peer_names").remove(server_name)


@app.route("/hold_election/<id>")
def hold_election(id = None):
    """
    Bully Algorithm to elect primary server
    """
    # ID with highest number
    peer_ids = app.config.get("peer_ids")
    # When a server is transferred an election to hold from another server.
    # Add the transferring server to peer list if it's not already there.
    if id and "Catalog_" + id not in app.config.get("peer_names"):
        app.config.get("peer_names").append("Catalog_" + id)

    primary_id = max(peer_ids)

    # Current server has the highest ID. self-elected as primary
    # and notify others
    if app.config["id"] == primary_id:
        app.config["primary"] = app.config.get("name")
        print("I won the election")
        notify_all()
        return Response(app.config.get("name") + " won", status=200)
    else:
        candidates = get_candidates(peer_ids, app.config["id"])

        for candidate_id in candidates:
            server_name = string_builder(["Catalog_"], candidate_id)
            root_url = get_root_url(app.config.get("server_dict"), server_name)
            request_url = string_builder([root_url], "hold_election/", app.config["id"])

            try:
                # Transfer the election to the first successful connected candidate
                r = requests.get(request_url)
                return r.text

            except requests.exceptions.ConnectionError:
                if server_name in app.config.get("peer_names"):
                    app.config.get("peer_names").remove(server_name)

        # No server with higher IDs, elected by default
        app.config["primary"] = app.config.get("name")
        notify_all()
        print("I won the election")
        return Response(app.config.get("name") + " won", status=200)


@app.route("/register/<server_name>", methods=["PUT"])
def register(server_name):
    if server_name not in app.config.get("peer_names"):
        app.config.get("peer_names").append(server_name)
    return "Sucessfully register with " + app.config.get("name")


def sync_up(server_dict, peer_name_ids):
    """
    sync up with the first available server
    """
    for peer_name_id in peer_name_ids:
        if peer_name_id[0] != app.config.get("name"):
            peer_root_url = get_root_url(server_dict, peer_name_id[0])
            try:
                # Send a request to root to see if this peer is up.
                # It will respond with 404 but that doesn't matter
                requests.get(peer_root_url)
                original_db = string_builder(["inventory_"], peer_name_id[1], ".db")
                target_db = string_builder(["inventory_"], app.config["id"], ".db")
                subprocess.call(['bash','copy.sh', original_db, target_db])
                print(string_builder([], "sync up with ", peer_name_id[1]))
                return
            except requests.exceptions.ConnectionError:
                print(peer_name_id[0], " not running")


def register_with_frontend(server_dict):
    frontend_root_url = get_root_url(server_dict, "Frontend")
    register_query = string_builder([frontend_root_url], "notify/", "Catalog/", app.config["id"])
    try:
        requests.put(register_query)
    except requests.exceptions.ConnectionError:
        print("Frontend is not running")

if __name__ == "__main__":
    app.config["id"] = sys.argv[1]
    app.config["name"] = "Catalog_" + app.config["id"]
    app.config["server_dict"] = get_server_dict("server_config", ["Order", "Client"])
    # Redundant variable assignment make the calls to this reference shorter
    server_dict = app.config["server_dict"]
    replica_names, replica_ids = zip(*get_replicas(server_dict, "Catalog"))
    app.config["peer_ids"] = list(replica_ids)
    # Assume a primary, if the assumed primary isn't in fact running, another
    # primary will be elected later on
    app.config["primary"] = "Catalog_" + str(max(app.config["peer_ids"]))
    app.config["peer_names"] = list(replica_names)
    catalog_ip, catalog_port = get_id_port(server_dict, "Catalog", app.config.get("id"))

    root_url = get_root_url(app.config.get("server_dict"), app.config["name"])
    # executors = ThreadPoolExecutor(max_workers=1)
    # executors.submit(hold_election)
    sync_up(server_dict, list(get_replicas(server_dict, "Catalog")))
    register_with_frontend(server_dict)
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(app.run, host=catalog_ip, port=catalog_port)
        executor.submit(hold_election)
        # app.run(host=catalog_ip, port=catalog_port)



