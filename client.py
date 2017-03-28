# -*- coding"utf-8 -*-
import logging
import time
import sys
import socket
from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import *
from kazoo.protocol.states import EventType
from functools import partial
import thread

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(filename='client.log', format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger("zookeeper")
ROOT_PATH = '/'
SERVICE_PATH = 'services'
SERVICE_VALUE = 'service value'
SERVICE_AVAILABLE = True
CONNECT_STRING = '127.0.0.1:2181'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 23412

zk = KazooClient(hosts=CONNECT_STRING)
G_SERVICE_DICT = {}  # Global dictionary to store Available Service.
G_REGISTERED_VALUE_PATH = {}
G_REGISTERED_CHILDREN_PATH = {}


#  create listener
def my_listener(state):
    if state == KazooState.LOST:
        SERVICE_AVAILABLE = False
        print "[STATE] Lost."
    elif state == KazooState.SUSPENDED:
        SERVICE_AVAILABLE = False
        print '[STATE] Suspended.'
    elif state == KazooState.CONNECTED:
        SERVICE_AVAILABLE = True
        print '[STATE] CONNECTED.'


def initialize_child_watch(path):
    if path not in G_REGISTERED_CHILDREN_PATH:
        G_REGISTERED_CHILDREN_PATH[path] = 1

        @zk.ChildrenWatch(path)
        def child_watch_services(children):
            for child in children:
                child_path = path+'/'+child
                initialize_value_watch(child_path)
                logger.info('Try appending new child: ' + str(child))
    else:
        logger.info("Path existed in children path.")


def initialize_value_watch(path):
    if path not in G_REGISTERED_VALUE_PATH:
        G_REGISTERED_VALUE_PATH[path] = 1

        @zk.DataWatch(path)
        def value_watch_services(data, stat, event):
            print '-- value watch --'
            print data, path
            print stat
            print event
            if event:
                print event.type, event.path
                if event.type == EventType.CREATED:
                    try:
                        logger.info("Recreate Path in watching path : " + path + ' ,data : ' + str(data))
                        G_SERVICE_DICT[path] = data
                    except KeyError:
                        logger.error('Key error : ' + path + ' in G_SERVICE_DICT when create_event')
                elif event.type == EventType.CHANGED:
                    try:
                        logger.info("Data Reset. Path : " + path + ' ,data before :' + str(G_SERVICE_DICT[path])
                                    + ', after : ' + data)
                        G_SERVICE_DICT[path] = data
                    except KeyError:
                        logger.error('Key error : ' + path + ' in G_SERVICE_DICT when change_event')
                elif event.type == EventType.DELETED:
                    try:
                        del G_SERVICE_DICT[path]
                    except KeyError:
                        logger.error('Key error : ' + path + 'in G_SERVICE_DICT when delete_event')
                else:
                    logger.error('Unhandled event type in value watch, type : ' + str(event.type))
            else:
                logger.info("Create for first time.")
                try:
                    G_SERVICE_DICT[path] = data
                    print '=====', path, data
                except KeyError:
                    logger.error('Key error in None event in value watch.')
            print G_SERVICE_DICT
    else:
        logger.info('Path existed in value path.')


# get service children paths' value callback
def get_service_child_value_callback(child_path, async_obj):
    try:
        value, node_stat = async_obj.get()
        logger.info("Child Value: " + str(value) + ', Node_stat: ' + str(node_stat))
        if child_path not in G_SERVICE_DICT:
            G_SERVICE_DICT[child_path] = value
        else:
            G_SERVICE_DICT[child_path] = value
            logger.error("Key existed in dict.")
        initialize_value_watch(child_path)
    except NoNodeError:
        logger.error(NoNodeError.message)
    except ZookeeperError:
        logger.error(ZookeeperError.message)


# get service_path '/SERVICE_PATH' callback
def get_service_path_children_callback(async_obj):
    try:
        children = async_obj.get()
        logger.info('Service Children here: ' + str(children))
        if children:  # children is not empty.
            for child in children:
                get_service_child_value = zk.get_async(ROOT_PATH+SERVICE_PATH+'/'+child)
                get_service_child_value.rawlink(partial(get_service_child_value_callback,
                                                        ROOT_PATH+SERVICE_PATH+'/'+child))
        else:
            logger.debug('Empty Children Path.')
        initialize_child_watch(ROOT_PATH+SERVICE_PATH)
    except (ConnectionLossException, NoAuthException):
        logger.error('Can not connect.')
        sys.exit(1)


#  Create Service path callback
def create_path_async_callback(async_obj):
    try:
        result = async_obj.get()
        logger.info('create path result: ' + str(result))
        initialize_child_watch(ROOT_PATH+SERVICE_PATH)
    except NodeExistsError:
        logger.error(NodeExistsError.message)
    except NoNodeError:
        logger.error(NoNodeError.message)
    except ZookeeperError:
        logger.error(ZookeeperError.message)


# get root '/' path callback
def get_root_children_async_callback(async_obj):
    try:
        children = async_obj.get()
        logger.info('Children here : ' + str(children))
        if SERVICE_PATH not in children:
            create_service_path = zk.create_async(path=ROOT_PATH+SERVICE_PATH, value=SERVICE_VALUE)
            create_service_path.rawlink(create_path_async_callback)
        else:
            get_service_children = zk.get_children_async(path=ROOT_PATH+SERVICE_PATH)
            get_service_children.rawlink(get_service_path_children_callback)
    except (ConnectionLossException, NoAuthException):
        logger.error('Can not connect.')
        sys.exit(1)


def handle_new_conn(con):
    while True:
        data = con.recv(1024)
        if not data:
            break
        if data == 'services':
            print 'get services'
            con.send(str(G_SERVICE_DICT))
    con.close()

if __name__ == '__main__':
    zk.start()
    zk.add_listener(my_listener)
    get_children_async_obj = zk.get_children_async(ROOT_PATH)
    get_children_async_obj.rawlink(get_root_children_async_callback)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((SOCKET_HOST, SOCKET_PORT))
    except socket.error, msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
    s.listen(10)
    while True:
        conn, addr = s.accept()
        # conn.settimeout(30)
        print 'Connected with ' + addr[0] + ':' + str(addr[1])
        thread.start_new_thread(handle_new_conn, (conn,))

