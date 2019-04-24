#!/bin/bash
echo Make sure servers are up and running first

wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &
wget -qO- http://128.119.243.147:7001/buy/2 &

sleep 3
echo 'fuser -k 7001/tcp' | ssh $1@elnux1.cs.umass.edu
wget -qO- http://128.119.243.164:7005/buy/1 &
wget -qO- http://128.119.243.164:7005/buy/3 &
wget -qO- http://128.119.243.164:7005/buy/2 &
wget -qO- http://128.119.243.164:7005/buy/4 &
wget -qO- http://128.119.243.164:7005/buy/5 &
wget -qO- http://128.119.243.164:7005/buy/6 &

sleep 3
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 7001/tcp; python3 Order.py 0' | ssh $1@elnux1.cs.umass.edu



