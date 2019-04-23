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


def string_builder(l, *elements) -> str:
    """
    :param l: a list of strings
    :param elements: strings
    :return:
    """
    l.extend(elements)

    return "".join(l)


def get_server_dict(server_config, exclude_types=[]):

    with open(server_config, mode='r') as server_file:

        server_dict = {}
        csv_reader = csv.DictReader(server_file)

        for row in csv_reader:
            server_name = row['Server']
            exclude = False
            for exclude_type in exclude_types:
                if exclude_type in server_name:
                    exclude = True
                    break

            if not exclude:
                server_dict[server_name] = {'Machine': row['Machine'],
                                            'IP': row['IP'],
                                            'Port': row['Port'],
                                            'ID' : row['Replica_num']}

    return server_dict


def get_id_port(server_dict, component_name: str, component_n: str = None) -> (str, str):
    """
    Get ID and port of a server from the config file

    :param server_dict: dictionary that stores server configs
    :param component_name: name of the component, could be Frontend, Catalog or Order.
    :param component_n: its replica id, if not provided, only component_name is used to search the config file
    :return: ip and port specified in config file
    """

    if component_n:
        component_id = string_builder([], component_name, "_", component_n)
    else:
        component_id = component_name

    ip = server_dict[component_id]['IP']
    port = server_dict[component_id]['Port']

    return ip, port

def get_root_url(serverdict, server_name, server_n = None):
    """
    Get root url in the form of http://ip:port/ of the specified server
    """
    ip, port = get_id_port(serverdict,server_name, server_n)
    root_url = string_builder(["http://"], ip, ":", port, "/")

    return root_url

def get_replicas(server_dict, server_type):
    replica_names = []
    replica_ids = []

    for server_name, server_settings in server_dict.items():
        if server_type in server_name:
            replica_names.append(server_name)
            replica_ids.append(server_settings['ID'])

    return zip(replica_names, replica_ids)
