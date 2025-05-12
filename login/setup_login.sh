#!/bin/bash

echo "===== 设置登录系统 ====="

# 检查MySQL是否安装
if ! command -v mysql &> /dev/null; then
    echo "错误: MySQL未安装。请先安装MySQL服务器。"
    exit 1
fi

# 设置数据库
echo "设置数据库..."
read -p "请输入MySQL root密码 (直接回车如果没有密码): " root_pass

if [ -z "$root_pass" ]; then
    mysql < setup_login_db.sql
else
    mysql -u root -p"$root_pass" < setup_login_db.sql
fi

if [ $? -ne 0 ]; then
    echo "错误: 数据库设置失败。"
    exit 1
fi
echo "数据库设置成功！"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败。请确保已安装Python 3。"
        exit 1
    fi
fi

# 激活虚拟环境并安装依赖
echo "安装依赖..."
source venv/bin/activate
pip install Flask==2.0.1 Werkzeug==2.0.1 mysql-connector-python==8.0.26 flask-cors==3.0.10 google-auth

# 检查端口占用
port_pid=$(lsof -ti:5001)
if [ ! -z "$port_pid" ]; then
    echo "端口5001已被占用，正在关闭进程..."
    kill -9 $port_pid
fi

echo "===== 设置完成 ====="
echo ""
echo "要启动后端服务，请运行:"
echo "cd $(pwd) && source venv/bin/activate && python backend.py"
echo ""
echo "要打开前端页面，请在另一个终端窗口运行:"
echo "open $(pwd)/frontend.html"
echo ""
echo "或者直接在浏览器中打开frontend.html文件"
echo "===== 祝使用愉快！ =====" 