# User Management System

This is a simple user management system that provides CRUD functionality for users, including a frontend interface and backend API.

## Features

- User list display with pagination
- Add new users
- Edit user information
- Delete users
- Search users
- Admin privilege management

## Tech Stack

- Frontend: HTML, CSS, JavaScript, Bootstrap 5, jQuery
- Backend: Python, Flask
- Database: MySQL

## Installation and Setup

### Prerequisites

- Python 3.7+
- MySQL 5.7+
- Dependencies (will be installed from requirements.txt in the login directory)

### Installation Steps

1. Navigate to the `admin_user` directory:
   ```
   cd admin_user
   ```

2. Run the setup script:
   ```
   chmod +x setup.sh
   ./setup.sh
   ```

   This script will:
   - Create or use an existing Python virtual environment
   - Install all dependencies
   - Update the database structure
   - Start the backend service

## Usage

1. Start the backend service (not needed if setup.sh has already been run):
   ```
   python3 backend.py
   ```

2. Open the frontend.html file in your browser

3. Log in with the default admin account:
   - Username: admin
   - Password: 123

## API Documentation

### Get User List

- **URL**: `/api/admin/users`
- **Method**: `GET`
- **Parameters**:
  - `page`: Page number (default is 1)
  - `per_page`: Items per page (default is 10)
- **Response Example**:
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

### Get Single User

- **URL**: `/api/admin/users/<user_id>`
- **Method**: `GET`
- **Response Example**:
  ```json
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "created_at": "2023-05-10T12:30:45",
    "is_admin": true
  }
  ```

### Create User

- **URL**: `/api/admin/users`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "test_user",
    "password": "password123",
    "email": "user@example.com",
    "is_admin": false
  }
  ```
- **Response Example**:
  ```json
  {
    "message": "User created successfully"
  }
  ```

### Update User

- **URL**: `/api/admin/users/<user_id>`
- **Method**: `PUT`
- **Request Body**:
  ```json
  {
    "username": "updated_username",
    "email": "updated@example.com",
    "password": "new_password",
    "is_admin": true
  }
  ```
- **Response Example**:
  ```json
  {
    "message": "User updated successfully"
  }
  ```

### Delete User

- **URL**: `/api/admin/users/<user_id>`
- **Method**: `DELETE`
- **Response Example**:
  ```json
  {
    "message": "User deleted successfully"
  }
  ```

### Search Users

- **URL**: `/api/admin/search-users`
- **Method**: `GET`
- **Parameters**:
  - `keyword`: Search keyword
- **Response Example**:
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

## Database Updates

The system will automatically add the following fields to the users table:
- `is_admin`: Indicates whether the user has admin privileges
- `created_at`: User creation timestamp

If you need to update the database manually, you can run:
```
mysql -u taotao -p123456 < setup_admin_db.sql
```

## Notes

- This system is for demonstration purposes only; additional security measures should be added before using in production
- Do not store admin passwords in plain text
- In real-world usage, a proper user authentication mechanism should be implemented 