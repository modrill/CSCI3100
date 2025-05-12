#!/bin/bash

# 显示彩色输出的函数
function print_color() {
    case $1 in
        "green") echo -e "\033[0;32m$2\033[0m" ;;
        "red") echo -e "\033[0;31m$2\033[0m" ;;
        "yellow") echo -e "\033[0;33m$2\033[0m" ;;
        *) echo $2 ;;
    esac
}

# 检查Python是否已安装
print_color "yellow" "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    print_color "red" "未安装Python3，请先安装Python3"
    exit 1
fi
print_color "green" "Python3已安装"

# 检查pip是否已安装
if ! command -v pip3 &> /dev/null; then
    print_color "red" "未安装pip3，请先安装pip3"
    exit 1
fi
print_color "green" "pip3已安装"

# 检查虚拟环境
VENV_DIR="../login/venv"
if [ ! -d "$VENV_DIR" ]; then
    print_color "yellow" "未找到虚拟环境，创建新的虚拟环境..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        print_color "red" "创建虚拟环境失败，请检查Python是否正确安装"
        exit 1
    fi
    print_color "green" "虚拟环境创建成功"
else
    print_color "green" "使用已有的虚拟环境"
fi

# 激活虚拟环境
print_color "yellow" "激活虚拟环境..."
source $VENV_DIR/bin/activate
if [ $? -ne 0 ]; then
    print_color "red" "激活虚拟环境失败"
    exit 1
fi
print_color "green" "虚拟环境激活成功"

# 安装依赖
print_color "yellow" "安装所需依赖..."
pip3 install -r ../login/requirements.txt
if [ $? -ne 0 ]; then
    print_color "red" "安装依赖失败"
    exit 1
fi
print_color "green" "依赖安装成功"

# 检查MySQL是否已安装
print_color "yellow" "检查MySQL服务..."
if ! command -v mysql &> /dev/null; then
    print_color "red" "未安装MySQL，请先安装MySQL"
    exit 1
fi
print_color "green" "MySQL已安装"

# 执行SQL脚本更新数据库
print_color "yellow" "更新数据库结构..."
mysql -u taotao -p123456 < setup_admin_db.sql
if [ $? -ne 0 ]; then
    print_color "red" "数据库更新失败，请检查MySQL连接和权限"
    exit 1
fi
print_color "green" "数据库更新成功"

# 启动后端服务
print_color "yellow" "正在启动管理用户后端服务..."
python3 backend.py &
if [ $? -ne 0 ]; then
    print_color "red" "启动后端服务失败"
    exit 1
fi
print_color "green" "后端服务已在后台启动，端口5002"

print_color "green" "======================="
print_color "green" "管理用户系统设置完成！"
print_color "green" "API地址: http://localhost:5002/api/admin/users"
print_color "green" "前端地址: 使用浏览器访问 frontend.html"
print_color "green" "=======================" 