#!/bin/bash
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 6001/tcp; python3 Order.py 0' | ssh $1@elnux7.cs.umass.edu &
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 6002/tcp; python3 Catalog.py 0' | ssh $1@elnux2.cs.umass.edu &
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 6003/tcp; python3 Frontend.py' | ssh $1@elnux3.cs.umass.edu &
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 6005/tcp; python3 Order.py 1' | ssh $1@elnux2.cs.umass.edu &
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 6006/tcp; python3 Catalog.py 1' | ssh $1@elnux1.cs.umass.edu