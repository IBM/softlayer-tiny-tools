#!/bin/bash

# 检查test1环境变量是否存在于/etc/profile中
if ! grep -q "export $1=" /etc/profile; then
    echo "$1 not in env and add it to /etc/profile"
    echo "export $1=\"$2\"" | sudo tee -a /etc/profile > /dev/null
    # 如果需要在当前会话中立即生效，请取消下面的注释
    source /etc/profile
else
    echo "$1 already in /etc/profile"
fi

