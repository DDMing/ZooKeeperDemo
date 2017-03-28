# -*- coding"utf-8 -*-
from MySocket import *
import time

SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 23412

socket = mysocket()
socket.connect(SOCKET_HOST, SOCKET_PORT)
socket.mysend('services')
while 1:
    reply = socket.myreceive()
    if reply:
        print reply
        break
    else:
        print "null"
    time.sleep(1)
socket.close()
