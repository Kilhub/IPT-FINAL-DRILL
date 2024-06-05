import unittest
import json
import jwt
import datetime
from api import app, mysql

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.headers = {'Content-Type': 'application/json'}

        # Create a token for testing
        self.token = jwt.encode({'user': 'admin', 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                                app.config['SECRET_KEY'], algorithm="HS256")
        self.auth_headers = {'x-access-token': self.token}

    def test_login_success(self):
        response = self.app.post('/login', auth=('admin', 'admin123'))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('token', data)

    def test_login_failure(self):
        response = self.app.post('/login', auth=('admin', 'wrongpassword'))
        self.assertEqual(response.status_code, 401)

    def test_token_missing(self):
        response = self.app.get('/customers/search')
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['message'], 'Token is missing!')

    def test_token_invalid(self):
        headers = {'x-access-token': 'invalidtoken'}
        response = self.app.get('/customers/search', headers=headers)
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['message'], 'Token is invalid!')

    def test_search_customers_success(self):
        with app.app_context():
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO Customers (FirstName, LastName, PhoneNumber, Email, MembershipStatus) VALUES (%s, %s, %s, %s, %s)", 
                        ("John", "Doe", "1234567890", "john.doe@example.com", "Gold"))
            mysql.connection.commit()
            cur.close()

        response = self.app.get('/customers/search?id=1', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_search_customers_missing_id(self):
        response = self.app.get('/customers/search', headers=self.auth_headers)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['message'], 'Missing id parameter')

    def test_search_customers_not_found(self):
        response = self.app.get('/customers/search?id=99999', headers=self.auth_headers)
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data['message'], 'Customer not found')

    def test_create_customer_success(self):
        customer_data = {
            "FirstName": "John",
            "LastName": "Doe",
            "PhoneNumber": "1234567890",
            "Email": "john.doe@example.com",
            "MembershipStatus": "Gold"
        }
        response = self.app.post('/customers', json=customer_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['message'], 'Customer added successfully')

    def test_create_customer_missing_fields(self):
        customer_data = {
            "FirstName": "John",
            "LastName": "Doe",
            "PhoneNumber": "1234567890"
        }
        response = self.app.post('/customers', json=customer_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['message'], 'Missing required fields')

    def test_update_customer_success(self):
        customer_data = {
            "FirstName": "Jane",
            "LastName": "Doe",
            "PhoneNumber": "9876543210",
            "Email": "jane.doe@example.com",
            "MembershipStatus": "Platinum"
        }
        response = self.app.put('/customers/1', json=customer_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Customer updated successfully')

    def test_delete_employee_success(self):
        with app.app_context():
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO Employees (FirstName, LastName, Position, Salary) VALUES (%s, %s, %s, %s)", 
                        ("John", "Doe", "Manager", 50000))
            mysql.connection.commit()
            employee_id = cur.lastrowid
            cur.close()

        response = self.app.delete(f'/employees/{employee_id}', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'Employee item deleted successfully')

if __name__ == '__main__':
    unittest.main()
