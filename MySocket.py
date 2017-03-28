# -*- coding: utf-8 -*-
import socket
MSGLEN = 4096


class mysocket:
    '''demonstration class only
      - coded for clarity, not efficiency
    '''

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    def mysend(self, msg):
        msglen = len(msg)
        totalsent = 0
        while totalsent < msglen:
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent
        print 'send over'

    def myreceive(self):
        try:
            recv_data = self.sock.recv(1024)
        except socket.error:
            return None
        return recv_data

    def close(self):
        self.sock.close()
