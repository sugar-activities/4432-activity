import time
lst = range(25)
count = 0
next = int(time.time() + 30)
last = int(time.time())
while next > int(time.time()):
    test = int(next-time.time())
    if test < last:
       last = test
       print last       

