# 677 Lab 3

Docker containers:

1. Go into src folder.
2. Run ./docker_build.sh to build docker images for all 5 components.

4. Run docker network create 677network. This operation is neccessary because a docker container that's running on default Bridge network doesn't benefit for docker's internal DNS lookup. We obeserved that it takes a long time for default bridge netowrk to resolve an IP and therefore every HTTP request is extrememly slow

4. To run each component

  Catalog_0:
    docker run --name catalog_0 --net=677network -i -t -p 6001:6001 catalog:0 <br />
    #In the docker container, execute the following <br />
    python3 Catalog.py 0 <br />
      
  Catalog_1:
    docker run --name catalog_1 --net=677network -i -t -p 6002:6002 catalog:1 <br />
    #In the docker container, execute the following <br />
    python3 Catalog.py 1 <br />
   
   Frontend 
    docker run --name frontend --net=677network -i -t -p 6003:6003 frontend:0 <br />
    #In the docker container, execute the following <br />
    python3 Frontend.py <br />
   
   Order_0
     docker run --name order_0 --net=677network -i -t -p 6004:6004 order:0 <br />
     #In the docker container, execute the following <br />
     python3 Order.py 0 <br />
     
   Order_1
    docker run --name order_1 --net=677network -i -t -p 6005:6005 order:1 <br />
        #In the docker container, execute the following <br />
    python3 Order.py 1 <br />

4. 
