#!/bin/bash
echo 'fuser -k 6001/tcp' | ssh $1@elnux7.cs.umass.edu &
echo 'fuser -k 6002/tcp' | ssh $1@elnux2.cs.umass.edu &
echo 'fuser -k 6003/tcp' | ssh $1@elnux3.cs.umass.edu &
echo 'fuser -k 6005/tcp' | ssh $1@elnux2.cs.umass.edu &
echo 'fuser -k 6006/tcp' | ssh $1@elnux1.cs.umass.edu