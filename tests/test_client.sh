#!/bin/bash
echo Testing same basic functionalities from lab 2
python3 ../src/Client.py lookup 1 
echo Buying first item 5 times
python3 ../src/Client.py buy 1
python3 ../src/Client.py buy 1
python3 ../src/Client.py buy 1
python3 ../src/Client.py buy 1
python3 ../src/Client.py buy 1
echo Looking up final stock of first item
python3 ../src/Client.py lookup 1 

python3 ../src/Client.py lookup 2 
echo Buying second item 5 times
python3 ../src/Client.py buy 2 
python3 ../src/Client.py buy 2 
python3 ../src/Client.py buy 2 
python3 ../src/Client.py buy 2 
python3 ../src/Client.py buy 2 
echo Looking up final stock of second item
python3 ../src/Client.py lookup 2 

python3 ../src/Client.py lookup 3 
echo Buying third item 5 times, starting at stock 4
python3 ../src/Client.py buy 3 
python3 ../src/Client.py buy 3 
python3 ../src/Client.py buy 3 
python3 ../src/Client.py buy 3 
python3 ../src/Client.py buy 3 
echo Looking up final stock of third item
python3 ../src/Client.py lookup 3 

python3 ../src/Client.py lookup 6 
echo Buying sixth item 5 times, starting at stock 3
python3 ../src/Client.py buy 6 
python3 ../src/Client.py buy 6 
python3 ../src/Client.py buy 6 
python3 ../src/Client.py buy 6 
python3 ../src/Client.py buy 6 
echo Looking up final stock of fourth item
python3 ../src/Client.py lookup 6 

echo Searching topic 'graduate_school'
python3 ../src/Client.py search graduate_school
echo Searching topic 'distributed_systems'
python3 ../src/Client.py search distributed_systems 
echo Done testing basic client operations!



