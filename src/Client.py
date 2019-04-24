import csv
import requests
import time
import sys
from utils import *
server_dict= get_server_dict("server_config", ["Order", "Client","Catalog"])
FRONTEND_ADDRESS = get_root_url(server_dict, "Frontend")


def search(topic, print_output = True):
    search_result = requests.get(FRONTEND_ADDRESS + '/search/' + topic).text
    if print_output:
        print(search_result)
    return search_result

def lookup(item_number, print_output = True):
    lookup_result = requests.get(FRONTEND_ADDRESS + '/lookup/' + str(item_number)).text
    if print_output:
        print(lookup_result)
    return lookup_result

def buy(catalog_id, print_output = True):
    buy_result = requests.get(FRONTEND_ADDRESS + '/buy/' + str(catalog_id)).text
    if print_output:
        print(buy_result)
    return buy_result

def sequential_query(query_fun, query_arg, iterations, write_file, client_name = ''):
    # if clients are named, then also save query printed outputs to file
    if len(client_name) > 0 :
        printed_file = open(write_file + '_' + 'printed.txt','w')

    total_runtime = 0
    with open(write_file + '.txt','w') as output_file:
        for i in range(iterations):
            start = time.time()
            output = query_fun(query_arg,print_output = False)
            runtime = time.time() - start
            total_runtime = total_runtime + runtime
            if len(client_name) > 0 :
                printed_file.write(client_name + ' ' + output + '\n')
            output_file.write(str(runtime)+ '\n')
        print('Average runtime is ' ) + str(1.0*total_runtime/iterations)



def main():
    command_fun_dict = {'buy':buy, 'search': search, 'lookup': lookup}
    call_string = sys.argv[1]
    call_function = command_fun_dict[call_string]
    call_argument = sys.argv[2]
    if len(sys.argv) > 3:
        iterations = int(sys.argv[3])
        if len(sys.argv) == 5:
            client_name = str(sys.argv[4])
        else:
            client_name = ''
        filename = '../test/experiment_results/' + client_name + call_string + '_' + str(call_argument) + '_' + str(iterations) 

        sequential_query(call_function,call_argument,iterations,filename,client_name)
        print ('Sequential ' + call_string + ' results written to ' + filename)
    else:
        call_function(call_argument)



if __name__ == '__main__':
    main()