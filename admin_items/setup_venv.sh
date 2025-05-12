#!/bin/bash

# 检查venv目录是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装所需依赖..."
pip install flask flask-cors mysql-connector-python

echo "虚拟环境设置完成！"
echo "现在可以运行 ./start_backend.sh 启动后端服务" 