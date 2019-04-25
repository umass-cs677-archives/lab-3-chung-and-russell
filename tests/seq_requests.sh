#!/bin/bash
curl http://128.119.243.147:6001/orders -X DELETE -v
curl http://128.119.243.164:6005/orders -X DELETE -v
echo Setting stocks to varying quantity and making 1000 buys
python3 ../src/Client.py buy 1 1000 c1 -hide
python3 ../src/Client.py buy 2 1000 c1 -hide
python3 ../src/Client.py buy 5 1000 c1 -hide
python3 ../src/Client.py buy 7 1000 c1 -hide

curl http://128.119.243.147:6001/orders -X DELETE -v
curl http://128.119.243.164:6005/orders -X DELETE -v
echo Looking up resulting stock
python3 ../src/Client.py lookup 1 1000 c1 -hide 
python3 ../src/Client.py lookup 2 1000 c1 -hide 
python3 ../src/Client.py lookup 5 1000 c1 -hide 
python3 ../src/Client.py lookup 7 1000 c1 -hide

curl http://128.119.243.147:6001/orders -X DELETE -v
curl http://128.119.243.164:6005/orders -X DELETE -v
echo Doing topic search lookup 1000 times
python3 ../src/Client.py search graduate_school 1000 c1 -hide
python3 ../src/Client.py search distributed_systems 1000 c1 -hide



