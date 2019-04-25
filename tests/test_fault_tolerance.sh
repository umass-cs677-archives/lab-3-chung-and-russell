#!/bin/bash
echo Make sure servers are up and running first
echo Querying both servers concurrently
curl -X PUT http://128.119.243.164:6002/update/1/quantity/set/500
curl -X PUT http://128.119.243.164:6002/update/2/quantity/set/400
curl -X PUT http://128.119.243.164:6002/update/3/quantity/set/300
curl -X PUT http://128.119.243.164:6002/update/4/quantity/set/200
curl -X PUT http://128.119.243.164:6002/update/5/quantity/set/100
curl -X PUT http://128.119.243.164:6002/update/6/quantity/set/500
curl -X PUT http://128.119.243.164:6002/update/7/quantity/set/0

python3 ../src/Client.py buy 1 &
python3 ../src/Client.py buy 1 &
python3 ../src/Client.py buy 1 &
python3 ../src/Client.py buy 1 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 2 &

sleep 1
echo Disabling primary order replica on server 1 and querying other server
fuser -k 6001/tcp
wget --spider http://128.119.243.164:6001/orders
python3 ../src/Client.py buy 1 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 3 &
python3 ../src/Client.py buy 4 &
python3 ../src/Client.py buy 5 &
python3 ../src/Client.py buy 6 &
python3 ../src/Client.py buy 7 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 3 &
python3 ../src/Client.py buy 6 &
python3 ../src/Client.py buy 1 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 3 &
python3 ../src/Client.py buy 4 &
python3 ../src/Client.py buy 5 &
python3 ../src/Client.py buy 6 &
python3 ../src/Client.py buy 7 &
python3 ../src/Client.py buy 2 &
python3 ../src/Client.py buy 3 &
python3 ../src/Client.py buy 6 &

sleep 1
echo Restarting replica on server 1 and verifying databases
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 6001/tcp; python3 Order.py 0' | ssh $1@elnux1.cs.umass.edu &

wget -qO- http://128.119.243.164:6005/check
wget -qO- http://128.119.243.147:6001/check

sleep 1



