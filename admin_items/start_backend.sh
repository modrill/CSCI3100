#!/bin/bash

# 提示用户输入MySQL密码
echo "请输入MySQL密码："
read -s DB_PASSWORD

# 数据库连接配置
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD="$DB_PASSWORD"
export DB_NAME=buyzu

echo "正在启动admin_items后端服务..."
echo "使用的数据库配置:"
echo "  HOST: $DB_HOST"
echo "  USER: $DB_USER"
echo "  DB: $DB_NAME"
echo ""

# 检查并激活虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
else
    echo "警告: 未找到虚拟环境，请先运行 ./setup_venv.sh"
    exit 1
fi

# 启动后端服务
cd "$(dirname "$0")"
python backend.py 