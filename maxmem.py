#!/tools/anacondapython-3.8.6/bin/python

import math

PROC= float(input("Enter the number of processors:  "))
QUEUE= input("Enter the queue name, s for standard, b2 for bigmem2, b4 for bigmem4:  ")

if QUEUE == "s":
	MAXMEM=192.0
elif QUEUE == "b2":
	MAXMEM=384.0
elif QUEUE == "b4":
	MAXMEM=768.0
else:
	print("Your queue", QUEUE, "specification was invalid")
MAXWORD=math.floor(( MAXMEM - 12.0 ) / ( PROC * 8.0 ) * ( 1024.0 ** 3.0 ) / ( 10.0 ** 6.0 ))

print(MAXWORD)
