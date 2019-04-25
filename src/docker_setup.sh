#!/bin/bash
rm docker_server
echo -e "Server,Machine,IP,Port,Replica_num" >> docker_server

ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' catalog_0)
port=6001
echo "Catalog_0,elnux2,${ip},${port},0" >> docker_server

ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' catalog_1)
port=6002
echo "Catalog_1,elnux2,${ip},${port},1" >> docker_server

ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' frontend)
port=6003
echo "Frontend,elnux2,${ip},${port},0" >> docker_server

ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' order_0)
port=6004
echo "Order_0,elnux2,${ip},${port},0" >> docker_server

ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' order_1)
port=6005
echo "Order_1,elnux2,${ip},${port},1" >> docker_server

docker cp docker_server catalog_0:/lab3/server_config
docker cp docker_server catalog_1:/lab3/server_config
docker cp docker_server order_0:/lab3/server_config
docker cp docker_server order_1:/lab3/server_config
docker cp docker_server frontend:/lab3/server_config



