 # webhook推送服务

 - cp ./conf-template.yaml  to /{宿主机目录}/config.yaml
 - 编辑 配置文件 /{宿主机目录}/config.yaml
 - 运行命令下列命令

```sh
docker pull sparkliu222/softlayer_webhook_notification:v1.6
 docker run  \
 -d -v /{宿主机目录}:/usr/src/app/config \
sparkliu222/softlayer_webhook_notification:v1.6
```