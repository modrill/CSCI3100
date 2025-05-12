# 用户管理系统

这是一个简单的用户管理系统，提供了用户的增删改查功能，包括前端界面和后端API。

## 功能特点

- 用户列表展示，支持分页
- 添加新用户
- 编辑用户信息
- 删除用户
- 搜索用户
- 管理员权限设置

## 技术栈

- 前端：HTML, CSS, JavaScript, Bootstrap 5, jQuery
- 后端：Python, Flask
- 数据库：MySQL

## 安装与设置

### 先决条件

- Python 3.7+
- MySQL 5.7+
- 依赖项（将从login目录的requirements.txt安装）

### 安装步骤

1. 进入`admin_user`目录：
   ```
   cd admin_user
   ```

2. 运行安装脚本：
   ```
   chmod +x setup.sh
   ./setup.sh
   ```

   此脚本将：
   - 创建或使用现有的Python虚拟环境
   - 安装所有依赖项
   - 更新数据库结构
   - 启动后端服务

## 使用说明

1. 启动后端服务（如果setup.sh已运行则无需执行）：
   ```
   python3 backend.py
   ```

2. 在浏览器中打开frontend.html文件

3. 使用以下默认管理员账号登录系统：
   - 用户名：admin
   - 密码：123

## API文档

### 获取用户列表

- **URL**: `/api/admin/users`
- **方法**: `GET`
- **参数**:
  - `page`: 页码（默认为1）
  - `per_page`: 每页条数（默认为10）
- **返回示例**:
  ```json
  {
    "users": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "created_at": "2023-05-10T12:30:45",
        "is_admin": true
      }
    ],
    "total": 1,
    "page": 1,
    "per_page": 10,
    "total_pages": 1
  }
  ```

### 获取单个用户

- **URL**: `/api/admin/users/<user_id>`
- **方法**: `GET`
- **返回示例**:
  ```json
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "created_at": "2023-05-10T12:30:45",
    "is_admin": true
  }
  ```

### 创建用户

- **URL**: `/api/admin/users`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "username": "test_user",
    "password": "password123",
    "email": "user@example.com",
    "is_admin": false
  }
  ```
- **返回示例**:
  ```json
  {
    "message": "用户创建成功"
  }
  ```

### 更新用户

- **URL**: `/api/admin/users/<user_id>`
- **方法**: `PUT`
- **请求体**:
  ```json
  {
    "username": "updated_username",
    "email": "updated@example.com",
    "password": "new_password",
    "is_admin": true
  }
  ```
- **返回示例**:
  ```json
  {
    "message": "用户更新成功"
  }
  ```

### 删除用户

- **URL**: `/api/admin/users/<user_id>`
- **方法**: `DELETE`
- **返回示例**:
  ```json
  {
    "message": "用户删除成功"
  }
  ```

### 搜索用户

- **URL**: `/api/admin/search-users`
- **方法**: `GET`
- **参数**:
  - `keyword`: 搜索关键词
- **返回示例**:
  ```json
  {
    "users": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "created_at": "2023-05-10T12:30:45",
        "is_admin": true
      }
    ]
  }
  ```

## 数据库更新

系统会自动添加以下字段到用户表：
- `is_admin`: 表示用户是否有管理员权限
- `created_at`: 用户创建时间

如果需要手动更新数据库，可以运行：
```
mysql -u taotao -p123456 < setup_admin_db.sql
```

## 注意事项

- 此系统仅用于演示目的，在生产环境中使用前需添加更多安全措施
- 请勿将管理员密码明文存储
- 在实际使用中，应实现完善的用户认证机制 