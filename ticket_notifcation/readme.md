 
 # 工单推送服务

 - cp ./conf-template.yaml  to /{宿主机目录}/config.yaml
 - 编辑 配置文件 /{宿主机目录}/config.yaml
 - 运行命令下列命令

```sh
 docker run  \
 -d -v /{宿主机目录}:/usr/src/app/config \
 sparkliu222/softlayer_ticket_notification:v1.1
```