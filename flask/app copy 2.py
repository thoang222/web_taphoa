from threading import Thread
import mysql.connector
from mysql.connector import pooling
import requests
import telebot
import re
import datetime
from mysql1 import mysql_data
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

def send_mess_tele(content: str):
    token = 'YOUR_TELEGRAM_BOT_TOKEN'
    group_id = '-1002027749340'
    try:
        bot = telebot.TeleBot(token=token)
        bot.send_message(chat_id=group_id, text=content)
    except Exception as e:
        print(f"Failed to send message: {e}")

class MyApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.valid_username = "nhothoang"
        self.valid_password = "km@123456"
        self.app.secret_key = 'nhothoang'
        ######################################################################
        self.host = "localhost"
        self.user = "root"
        self.password = "123456"
        self.database_name = "user_data"
        self.table_name = "customers"
        #####################################
        # Cấu hình connection pool
        self.dbconfig = {
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "database": self.database_name
        }
        self.cnxpool = pooling.MySQLConnectionPool(pool_name="mypool",
                                                   pool_size=5,
                                                   **self.dbconfig)

        self.create_database()
        self.define_routes()

    def get_db_connection(self):
        return self.cnxpool.get_connection()
    
    def create_database(self):
        mysql_instance = mysql_data(self.host, self.user, self.password, self.database_name, self.table_name)
        Thread(target=mysql_instance.create_database).start()

    def define_routes(self):
        @self.app.route('/check')
        def index():
            if 'username' in session:
                return redirect(url_for('users_accounts'))
            return render_template('login1.html')

        @self.app.route('/login1', methods=['POST'])
        def login1():
            entered_username = request.form.get('username')
            entered_password = request.form.get('password')

            if entered_username == self.valid_username and entered_password == self.valid_password:
                session['username'] = entered_username
                return redirect(url_for('users_accounts'))
            else:
                return render_template('login1.html', error="Invalid username or password")

        @self.app.route('/login', methods=['GET', 'POST'])
        @self.app.route('/', methods=['GET', 'POST'])
        def login():
            msg = ''
            if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'uuid' in request.form:
                username = request.form['username']
                password = request.form['password']
                uuid = request.form['uuid']
                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f'SELECT * FROM {self.table_name} WHERE username = %s AND password = %s AND uuid = %s', (username, password, uuid))
                customer = cursor.fetchone()
                print(customer)
                if customer:
                    session['loggedin'] = True
                    session['id'] = customer['id']
                    session['username'] = customer['username']
                    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    msg = f'Logged in successfully/{current_date}/{customer["expdate"]}'
                    
                else:
                    msg = 'Incorrect username or password. Please try again.'
                cursor.close()
                conn.close()
            return render_template('login.html', msg=msg)

        @self.app.route('/register', methods=['GET', 'POST'])
        def register():
            msg = ''
            if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'phone' in request.form and 'address' in request.form and 'uuid' in request.form:
                username = request.form['username']
                password = request.form['password']
                phone = request.form['phone']
                address = request.form['address']
                uuid = request.form['uuid']
                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f'SELECT username FROM {self.table_name} WHERE username = %s', (username,))
                existing_user = cursor.fetchone()
                if existing_user:
                    if existing_user['username'] == username:
                        msg = 'Username already exists!'
                elif not re.match(r'[A-Za-z0-9]+', username):
                    msg = 'Username must contain only characters and numbers!'
                elif not username or not password:
                    msg = 'Please fill out the form!'
                else:
                    current_time = datetime.datetime.now().strftime('%Y-%m-%d')
                    cursor.execute(f'INSERT INTO {self.table_name} (username, password, phone ,address, expdate, uuid) VALUES (%s, %s, %s, %s, %s, %s)', (username, password,  phone, address,current_time, uuid))
                    conn.commit()
                    msg = 'You have successfully registered!'
                cursor.close()
                conn.close()
            return render_template('register.html', msg=msg)

        @self.app.route('/users_accounts', methods=['GET'])
        def users_accounts():
            if 'username' in session:
                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f"SELECT * FROM {self.table_name}")
                customers = cursor.fetchall()  
                cursor.close()
                conn.close()
                return render_template('users_accounts.html', customers=customers)
            else:
                return redirect(url_for('login'))

        @self.app.route('/update_customer', methods=['POST'])
        def update_customer():
            customer_id = request.form['id']
            username = request.form['username']
            password = request.form['password']
            phone = request.form['phone']
            address = request.form['address']
            expdate = request.form['expdate']
            uuid = request.form['uuid']
            inforuser = request.form['inforuser']
            timesapproval = request.form['timesapproval']
            notes = request.form['notes']

            update_query = """
            UPDATE customers SET 
                username = %s, 
                password = %s, 
                phone = %s, 
                address = %s, 
                expdate = %s, 
                uuid = %s, 
                inforuser = %s, 
                timesapproval = %s, 
                notes = %s 
            WHERE id = %s
            """
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(update_query, (username, password, phone, address, expdate, uuid, inforuser, timesapproval, notes, customer_id))
            conn.commit()
            cursor.close()
            conn.close()    

            return jsonify({'status': 'success'})

        @self.app.route('/delete_customer', methods=['POST'])
        def delete_customer():
            customer_id = request.form['id']

            delete_query = "DELETE FROM customers WHERE id = %s"
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(delete_query, (customer_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'status': 'success'})

        @self.app.route('/logout')
        def logout():
            session.pop('loggedin', None)
            session.pop('username', None)
            return redirect(url_for('login'))

    def run(self):
        self.app.run(debug=True)

# Create an instance of MyApp
app_instance = MyApp()
app = app_instance.app

if __name__ == "__main__":
    app_instance.run()
