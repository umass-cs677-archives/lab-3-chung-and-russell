from typing import List, Dict
from threading import Lock
import csv


def get_locks(n_lock: int):
    """"
    hard code locks for each row in the database
    """
    locks = []

    for i in range(n_lock):
        locks.append(Lock())

    return locks


def string_builder(l: List[str], *elements) -> str:
    """
    :param l: a list of strings
    :param elements: strings
    :return:
    """
    l.extend(elements)

    return "".join(l)


def get_server_dict(server_config: str) -> Dict[str, Dict[str, str]]:

    with open(server_config, mode='r') as server_file:

        server_dict: Dict[str, Dict[str, str]] = {}
        csv_reader = csv.DictReader(server_file)

        for row in csv_reader:
            server_name = row['Server']
            server_dict[server_name] = {'Machine': row['Machine'],
                                        'IP': row['IP'],
                                        'Port': row['Port']}

    return server_dict


def get_id_port(server_config: str, component_name: str, component_n: str = None) -> (str, str):
    """
    Get ID and port of a server from the config file

    :param server_config: name of the server config file
    :param component_name: name of the component, could be Frontend, Catalog or Order
    :param component_n: its replica id
    :return: ip and port specified in config file
    """

    server_dict = get_server_dict(server_config)

    if component_n:
        component_id = string_builder([], component_name, "_", component_n)
    else:
        component_id = component_name

    ip = server_dict[component_id]['IP']
    port = server_dict[component_id]['Port']

    return ip, port


def get_replicas(server_dict, server_type):
    replicas = set()

    for server_name in server_dict:
        if server_type in server_name:
            replicas.add(server_name)

    return replicas
