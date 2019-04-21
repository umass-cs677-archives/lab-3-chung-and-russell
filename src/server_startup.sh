#!/bin/bash
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 5001/tcp; python Order.py' | ssh $1@elnux1.cs.umass.edu &
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 5002/tcp; python Catalog.py' | ssh $1@elnux2.cs.umass.edu &
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 5003/tcp; python Frontend.py' | ssh $1@elnux3.cs.umass.edu &
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 5001/tcp; python Order.py' | ssh $1@elnux2.cs.umass.edu &
echo 'cd cs677/lab-3-chung-and-russell/src ; fuser -k 5003/tcp; python Catalog.py' | ssh $1@elnux1.cs.umass.edu &