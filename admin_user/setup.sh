#!/bin/bash

# Function to print colored output
function print_color() {
    case $1 in
        "green") echo -e "\033[0;32m$2\033[0m" ;;
        "red") echo -e "\033[0;31m$2\033[0m" ;;
        "yellow") echo -e "\033[0;33m$2\033[0m" ;;
        *) echo $2 ;;
    esac
}

# Check if Python is installed
print_color "yellow" "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    print_color "red" "Python3 is not installed, please install Python3 first"
    exit 1
fi
print_color "green" "Python3 is installed"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_color "red" "pip3 is not installed, please install pip3 first"
    exit 1
fi
print_color "green" "pip3 is installed"

# Check virtual environment
VENV_DIR="../login/venv"
if [ ! -d "$VENV_DIR" ]; then
    print_color "yellow" "Virtual environment not found, creating a new one..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        print_color "red" "Failed to create virtual environment, please check if Python is correctly installed"
        exit 1
    fi
    print_color "green" "Virtual environment created successfully"
else
    print_color "green" "Using existing virtual environment"
fi

# Activate virtual environment
print_color "yellow" "Activating virtual environment..."
source $VENV_DIR/bin/activate
if [ $? -ne 0 ]; then
    print_color "red" "Failed to activate virtual environment"
    exit 1
fi
print_color "green" "Virtual environment activated successfully"

# Install dependencies
print_color "yellow" "Installing required dependencies..."
pip3 install -r ../login/requirements.txt
if [ $? -ne 0 ]; then
    print_color "red" "Failed to install dependencies"
    exit 1
fi
print_color "green" "Dependencies installed successfully"

# Check if MySQL is installed
print_color "yellow" "Checking MySQL service..."
if ! command -v mysql &> /dev/null; then
    print_color "red" "MySQL is not installed, please install MySQL first"
    exit 1
fi
print_color "green" "MySQL is installed"

# Execute SQL script to update database
print_color "yellow" "Updating database structure..."
mysql -u taotao -p123456 < setup_admin_db.sql
if [ $? -ne 0 ]; then
    print_color "red" "Database update failed, please check MySQL connection and permissions"
    exit 1
fi
print_color "green" "Database updated successfully"

# Start backend service
print_color "yellow" "Starting user management backend service..."
python3 backend.py &
if [ $? -ne 0 ]; then
    print_color "red" "Failed to start backend service"
    exit 1
fi
print_color "green" "Backend service started in background, port 5002"

print_color "green" "======================="
print_color "green" "User Management System Setup Complete!"
print_color "green" "API URL: http://localhost:5002/api/admin/users"
print_color "green" "Frontend URL: Access frontend.html with your browser"
print_color "green" "=======================" 