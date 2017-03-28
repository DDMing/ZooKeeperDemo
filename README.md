# ZooKeeperDemo
Create a async process for Zookeeper. And a sync request for socket.

`需求`：希望利用zookeeper实现多台服务器的应用级的负载均衡。进程p作为负载均衡的监视进程，维护各个服务的ip:host以及可用的服务。进程q负责当前ip:host下的可用服务列表的更改。而进程r通过socket请求进程p，获取可用的服务。

目录下有四个文件
- MySocket.py - 封装Socket初始化，read，write的方法
- client.py - 执行监视zookeeper服务中的`SERVICE_PATH`目录下的子路径的创建以及监视子路径的值的改变。此为`需求`中的进程p
- add_services.py - 维护`SERVICE_PATH`下的本ip:host的可用服务的值。启动时进行创建，属性是`ephemeral`。现阶段在使用后可以直接手动输入新的值。此为`需求`中的进程q
- socket_client.py - 从进程p中获取维护的可用服务的列表。此为`需求`中的进程r。

演示示例:
 1. run zookeeper . (127.0.0.1:2181)
 2. call `python client.py`
 3. call `python add_services.py` ，然后就能看到client.py中的输出，看到改变的值。
 4. 在3中输入新的值，更改路径中的值，即可用得服务。
 5. call `python socket_client.py` 获取可用服务的结构体。
