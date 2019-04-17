from flask import Flask
import requests
import csv

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
    
    CATALOG_PORT = server_dict['Catalog']['Port']
    ORDER_PORT = server_dict['Order']['Port']
    FRONTEND_PORT = server_dict['Frontend']['Port']


CATALOG_QUERY = 'http://128.119.243.164:' + CATALOG_PORT + '/query/'
ORDER_BUY = 'http://128.119.243.147:' + ORDER_PORT + '/buy/'



@app.route("/search/<topic>", methods = ["GET"])
def search(topic):
    books = requests.get(CATALOG_QUERY + topic).json()

    search_result = []

    for book in books["items"]:
        search_result.append("Name: ")
        search_result.append(book)
        search_result.append(" Item ID: ")
        search_result.append(str(books["items"][book]))
        search_result.append("\n")

    return("".join(search_result))


@app.route("/lookup/<item_number>")
def lookup(item_number):
    books = requests.get(CATALOG_QUERY + item_number).json()

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


    return "".join(search_result)

@app.route("/buy/<catalog_id>")
def buy(catalog_id):
    response = requests.get(ORDER_BUY + catalog_id).json()

    if response["is_successful"]:
        return "bought book '" + response["title"] + "'\n"

    return "failed to buy book '" + response["title"] + "'\n"

if __name__ == "__main__":

    app.run(host='0.0.0.0',port = FRONTEND_PORT)
