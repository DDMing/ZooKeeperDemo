# -*- coding"utf-8 -*-
import logging
import time
import sys
from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import *
from functools import partial

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(filename='addservices.log', format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger("zookeeper")
ROOT_PATH = '/'
SERVICE_PATH = 'services'
MACHINE_STRING = '0.0.0.0:8080'
MACHINE_AVAIL_SERVICE = '1001;1002;1003'
SERVICE_AVAILABLE = True
CONNECT_STRING = '127.0.0.1:2181'

foredata = MACHINE_AVAIL_SERVICE

zk = KazooClient(hosts=CONNECT_STRING)
G_SERVICE_DICT = {}  # Global dictionary to store Available Service.


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


# get service children paths' value callback
def set_service_child_value_callback(child_path, async_obj):
    try:
        value, node_stat = async_obj.get()
        logger.info("Child Value: " + str(value) + ', Node_stat: ' + str(node_stat))
        if child_path not in G_SERVICE_DICT:
            G_SERVICE_DICT[child_path] = value
        else:
            G_SERVICE_DICT[child_path] = value
            logger.error("Key existed in dict.")
    except NoNodeError:
        logger.error(NoNodeError.message)
    except ZookeeperError:
        logger.error(ZookeeperError.message)


# Create Service path callback
def create_path_async_callback(async_obj):
    try:
        result = async_obj.get()
        logger.info('create path result: ' + str(result))
    except NodeExistsError:
        logger.error(NodeExistsError.message)
    except NoNodeError:
        logger.error(NoNodeError.message)
    except ZookeeperError:
        logger.error(ZookeeperError.message)


# get service_path '/SERVICE_PATH' callback
def get_service_path_children_callback(async_obj):
    try:
        children = async_obj.get()
        logger.info('Service Children here: ' + str(children))
        if 1:
            if MACHINE_STRING not in children:
                create_service_async_job = zk.create_async(path=ROOT_PATH+SERVICE_PATH+'/'+MACHINE_STRING,
                                                           value=MACHINE_AVAIL_SERVICE, ephemeral=True)
                create_service_async_job.rawlink(create_path_async_callback)
            else:
                print "PATH existed."
    except (ConnectionLossException, NoAuthException):
        logger.error('Can not connect.')
        sys.exit(1)


if __name__ == '__main__':
    zk.start()
    zk.add_listener(my_listener)
    get_children_async_obj = zk.get_children_async(ROOT_PATH+SERVICE_PATH)
    get_children_async_obj.rawlink(get_service_path_children_callback)
    while True:
        input_data = raw_input()
        if input_data != foredata:
            set_value_async = zk.set_async(path=ROOT_PATH+SERVICE_PATH+'/'+MACHINE_STRING, value=input_data)
            set_value_async.rawlink(partial(set_service_child_value_callback, input_data))
        if input_data == 'exit':
            print 'Exit'
            sys.exit(1)
        time.sleep(5)
