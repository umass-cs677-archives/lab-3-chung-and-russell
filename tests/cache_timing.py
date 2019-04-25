import csv
import requests
import time
import sys


CATALOG_WRITE = "http://128.119.243.168:6003/buy/1"
CATALOG_READ = "http://128.119.243.168:6003/lookup/1"



def main():
    # time writes without invalidation
    total_runtime = 0
    for i in range(100):
        start = time.time()
        requests.put(CATALOG_WRITE)
        runtime = time.time() - start
        total_runtime = total_runtime + runtime
    v1 = total_runtime/100.0

    # time writes with invalidation
    total_runtime = 0
    for i in range(100):
        requests.get(CATALOG_READ)
        requests.get(CATALOG_READ)
        start = time.time()
        requests.put(CATALOG_WRITE)
        runtime = time.time() - start
        total_runtime = total_runtime + runtime
    v2 = total_runtime/100.0

    # time reads with cache
    total_runtime = 0
    for i in range(100):
        start = time.time()
        requests.get(CATALOG_READ)
        runtime = time.time() - start
        total_runtime = total_runtime + runtime
    v3 = total_runtime/100.0

    # time reads with cache MISS
    total_runtime = 0
    for i in range(100):
        requests.put(CATALOG_WRITE)
        start = time.time()
        requests.get(CATALOG_READ)
        runtime = time.time() - start
        total_runtime = total_runtime + runtime
    v4 = total_runtime/100.0
    print([v1,v2,v3,v4])

    



if __name__ == '__main__':
    main()