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

def data_fetch(query, params=None):
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    data = cur.fetchall()
    cur.close()
    return data

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    # Dummy check for username and password (use database in production)
    if auth.username == 'admin' and auth.password == 'admin123':
        token = jwt.encode({'user': auth.username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                           app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})

    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

@app.route("/customers/search", methods=["GET"])
@token_required
def search_customers(current_user):
    customer_id = request.args.get('id')
    if customer_id is None:
        return jsonify({'message': 'Missing id parameter'}), 400
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Customers WHERE CustomerID = %s", (customer_id,))
    data = cur.fetchone()
    cur.close()
    if data:
        return jsonify(data), 200
    else:
        return jsonify({'message': 'Customer not found'}), 404

@app.route("/orders/search", methods=["GET"])
@token_required
def search_orders(current_user):
    order_id = request.args.get('id')
    if order_id is None:
        return jsonify({'message': 'Missing id parameter'}), 400
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Orders WHERE OrderID = %s", (order_id,))
    data = cur.fetchone()
    cur.close()
    if data:
        return jsonify(data), 200
    else:
        return jsonify({'message': 'Order not found'}), 404

@app.route("/menu/search", methods=["GET"])
@token_required
def search_menu(current_user):
    menu_item_id = request.args.get('id')
    if menu_item_id is None:
        return jsonify({'message': 'Missing id parameter'}), 400
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Menu WHERE MenuItemID = %s", (menu_item_id,))
    data = cur.fetchone()
    cur.close()
    if data:
        return jsonify(data), 200
    else:
        return jsonify({'message': 'Menu item not found'}), 404

@app.route("/payments/search", methods=["GET"])
@token_required
def search_payments(current_user):
    payment_id = request.args.get('id')
    if payment_id is None:
        return jsonify({'message': 'Missing id parameter'}), 400
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Payments WHERE PaymentID = %s", (payment_id,))
    data = cur.fetchone()
    cur.close()
    if data:
        return jsonify(data), 200
    else:
        return jsonify({'message': 'Payment not found'}), 404

@app.route("/employees/search", methods=["GET"])
@token_required
def search_employees(current_user):
    employee_id = request.args.get('id')
    if employee_id is None:
        return jsonify({'message': 'Missing id parameter'}), 400
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Employees WHERE EmployeeID = %s", (employee_id,))
    data = cur.fetchone()
    cur.close()
    if data:
        return jsonify(data), 200
    else:
        return jsonify({'message': 'Employee not found'}), 404

@app.route('/')
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/customers/<int:id>/orders', methods=['GET'])
@token_required
def get_customer_orders(current_user, id):
    query = """
    SELECT Customers.FirstName, Customers.LastName, Orders.OrderDate, Orders.TotalAmount
    FROM Customers
    INNER JOIN Orders ON Customers.CustomerID = Orders.CustomerID
    WHERE Customers.CustomerID = %s
    """
    data = data_fetch(query, (id,))
    return make_response(jsonify({"CustomerID": id, "count": len(data), "orders": data}), 200)

@app.route("/customers", methods=["POST"])
@token_required
def create_customers(current_user):
    data = request.json
    first_name = data.get('FirstName')
    last_name = data.get('LastName')
    phone_number = data.get('PhoneNumber')
    email = data.get('Email')
    membership_status = data.get('MembershipStatus')
    if not all([first_name, last_name, phone_number, email, membership_status]):
        return jsonify({'message': 'Missing required fields'}), 400
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Customers (FirstName, LastName, PhoneNumber, Email, MembershipStatus) VALUES (%s, %s, %s, %s, %s)", 
                (first_name, last_name, phone_number, email, membership_status))
    mysql.connection.commit()
    customer_id = cur.lastrowid
    cur.close()
    created_customer = {
        "CustomerID": customer_id,
        "FirstName": first_name,
        "LastName": last_name,
        "PhoneNumber": phone_number,
        "Email": email,
        "MembershipStatus": membership_status
    }
    return jsonify({'message': 'Customer added successfully', 'customer': created_customer}), 201

@app.route("/customers/<int:id>", methods=["PUT"])
@token_required
def update_customer(current_user, id):
    data = request.json
    first_name = data.get('FirstName')
    last_name = data.get('LastName')
    phone_number = data.get('PhoneNumber')
    email = data.get('Email')
    membership_status = data.get('MembershipStatus')
    if not all([first_name, last_name, phone_number, email, membership_status]):
        return jsonify({'message': 'Missing required fields'}), 400
    cur = mysql.connection.cursor()
    cur.execute("UPDATE Customers SET FirstName = %s, LastName = %s, PhoneNumber = %s, Email = %s, MembershipStatus = %s WHERE CustomerID = %s", 
                (first_name, last_name, phone_number, email, membership_status, id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Customer updated successfully'})

@app.route("/employees/<int:id>", methods=["DELETE"])
@token_required
def delete_employee(current_user, id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM employees WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Employee item deleted successfully'})

@app.route("/customers", methods=["GET"])
@token_required
def get_customers(current_user):
    data = data_fetch("SELECT * FROM Customers")
    return make_response(jsonify(data), 200)

@app.route("/orders", methods=["GET"])
@token_required
def get_orders(current_user):
    data = data_fetch("SELECT * FROM Orders")
    return make_response(jsonify(data), 200)

@app.route("/menu", methods=["GET"])
@token_required
def get_menu(current_user):
    data = data_fetch("SELECT * FROM Menu")
    return make_response(jsonify(data), 200)

@app.route("/payments", methods=["GET"])
@token_required
def get_payments(current_user):
    data = data_fetch("SELECT * FROM Payments")
    return make_response(jsonify(data), 200)

@app.route("/employees", methods=["GET"])
@token_required
def get_employees(current_user):
    data = data_fetch("SELECT * FROM Employees")
    return make_response(jsonify(data), 200)

if __name__ == "__main__":
    app.run(debug=True)
