BuyZu
This is GroupE's software engineering project for CSCI3100.The project Buyzu is a powerful online shopping platform.

Features

Admin

Manage Products
Manage Users
Manage Orders
Data Analytics

Client

Login/Registration
Browse Products with Details
Personalized Recommendations
Search Products
Shopping Cart
Checkout

How to Run

Requirements:

Download and install MySQL/MariaDB database service
Install Python 3.8 or higher
Download the project source code

Installation:

Extract the source code folder

Configure the database:

Start MySQL/MariaDB service, ensure it runs on port 3307
Open phpMyAdmin (http://localhost/phpmyadmin)
Create a new database named "buyzu"
Import the SQL file provided in the project


Project dependencies include:

# Web Framework
fastapi>=0.95.0
uvicorn>=0.22.0
jinja2>=3.1.2
python-multipart>=0.0.6
starlette>=0.27.0

# Database
pymysql>=1.0.3
mysql-connector-python>=8.0.33

# Authentication
google-auth>=2.22.0
werkzeug>=2.3.6

# Data Processing
numpy>=1.24.3
pandas>=2.0.1

# Email
pydantic[email]>=2.0.0


Start the application:

uvicorn reco_api_tt:app --reload --port 8000

Access the application in your browser:

Main page: http://localhost:8000/homepage.html
Search page: http://localhost:8000/searchpage.html
Admin dashboard: http://localhost:8000/admin

Project Structure

project_root/
├── images/          # Product images directory
│   ├── cat-electronics.jpeg
│   └── p1.jpeg...
├── static/          # Frontend static files
│   ├── homepage.html
│   └── cart.html...
└── item_vec.npy     # Auto-generated when running demo.py

Technology Stack

Database

MySQL/MariaDB: Using pymysql and mysql.connector for database connections
Port configuration: Database configured to run on port 3307

Web Framework

FastAPI: The main web framework used for building the API
Starlette: Used for session middleware and request handling (comes with FastAPI)

Authentication
Werkzeug: Used for password hashing and verification

Python Libraries

Data Processing
NumPy: Used for numerical operations and array handling
Pandas: For data manipulation and SQL query results processing

Email
smtplib: Standard library for sending emails
email.mime: For creating email content

Machine Learning
Recommendation models: The code references vector operations and recommendation algorithms