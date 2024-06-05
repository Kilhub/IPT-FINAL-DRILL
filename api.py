from flask import Flask, make_response, jsonify, request
from flask_mysqldb import MySQL
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

# MySQL configuration
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "mysql"
app.config["MYSQL_DB"] = "RestaurantDB"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_PORT"] = 3306
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

app.config['SECRET_KEY'] = 'admin123'

