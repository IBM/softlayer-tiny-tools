#!/bin/bash

# 检查test1环境变量是否存在于$3中
if ! grep -q "export $1=" $3; then
    echo "$1 not in env and add it to $3"
    echo "export $1=\"$2\"" | sudo tee -a $3 > /dev/null
    # 如果需要在当前会话中立即生效，请取消下面的注释
    source $3
else
    echo "$1 already in $3"
fi

