#!/bin/bash
echo Make sure servers are up and running first
wget --spider -q http://128.119.243.164:6005/buy/1 &
wget --spider -q http://128.119.243.164:6005/buy/1 &
wget --spider -q http://128.119.243.164:6005/buy/1 &
wget --spider -q http://128.119.243.164:6005/buy/1 &
wget --spider -q http://128.119.243.164:6005/buy/1 &
wget --spider -q http://128.119.243.147:6001/buy/2 &
wget --spider -q http://128.119.243.147:6001/buy/2 &
wget --spider -q http://128.119.243.147:6001/buy/2 &
wget --spider -q http://128.119.243.147:6001/buy/2 &
wget --spider -q http://128.119.243.147:6001/buy/2 &

sleep 2
wget -qO- http://128.119.243.164:6005/check
wget -qO- http://128.119.243.147:6001/check

echo can manually check each order DB for order consistency
echo http://128.119.243.164:6005/orders
echo http://128.119.243.147:6001/orders