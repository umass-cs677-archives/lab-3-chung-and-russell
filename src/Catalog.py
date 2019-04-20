import sqlite3
from threading import Lock
from flask import Flask, redirect, jsonify, abort, g
import csv
import sys
from utils import string_builder

SERVER_CONFIG = 'server_config'
with open(SERVER_CONFIG, mode ='r') as server_file:
    server_dict = {}
    csv_reader = csv.DictReader(server_file)
    for row in csv_reader:
        server_name = row['Server']
        server_dict[server_name] = {'Machine': row['Machine'],
                                    'IP': row['IP'],
                                    'Port': row['Port']}

    CATALOG_PORT = server_dict['Catalog_0']['Port']

app = Flask("catalog")

def _get_locks():
    """"
    hard code locks for each row in the database
    """
    locks = []

    for i in range(4):
        locks.append(Lock())

    return locks


locks = _get_locks()


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
    It pairs up entries of the dictionaries in the query result. For example, two dictionaries {a : "book1", b : 10} {a : "book2", b : 25}
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
    cursor = get_db(app.config.get("db_id")).cursor()

    if key == "topic":
        topic = (kwargs[key].replace("_", " "),)
        query_results = cursor.execute("SELECT name, id FROM books WHERE topic = ?", topic).fetchall()
        query_results = _pair_results(query_results, [("NAME", "ID")])
        response = jsonify(items=query_results)
    elif key == "item_number":

        with locks[kwargs[key] - 1]:
            query_result = cursor.execute("SELECT name, cost, quantity FROM books WHERE id = ?", str(kwargs[key])).fetchall()
            book_name = query_result[0]["NAME"]
            response = jsonify({book_name: _delete_keys(query_result[0],["NAME"])})

    else:
        return "no query criteria specified"

    return response


@app.route("/update/<item_number>/<field>/<operation>/<int:number>", methods=['GET','PUT'])
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

    conn = app.config.get("db_id")
    cursor = conn.cursor()
    success = True

    with locks[int(item_number) - 1]:
        if operation == "increase":
            cursor.execute("UPDATE books SET " + field + "=" + field + valid_operation[operation] + " ? WHERE ID = ?", [str(number), item_number])
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

        response = jsonify({book_name: _delete_keys(query_result[0], ["NAME"])})

    return response


if __name__ == "__main__":
    app.config["db_id"] = sys.argv[1]
    app.run(port = CATALOG_PORT)

