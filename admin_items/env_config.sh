#!/bin/bash

# 数据库连接配置
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=  # 密码留空，根据实际情况调整
export DB_NAME=buyzu

# 启动后端服务
cd "$(dirname "$0")"
python backend.py 