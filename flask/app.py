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
        self.valid_password = "nd@04121994"
        self.app.secret_key = 'nhothoang'
        ######################################################################
        self.host = "localhost"
        self.user = "root"
        self.password = "123456"
        self.database_name = "user_data"
        self.table_name = "customers"
        #####################################  
        # self.host = "root.cj42cemgqw9g.ap-southeast-1.rds.amazonaws.com"
        # self.user = "admin"
        # self.password = "km22071994"
        # self.database_name = "user_data"
        # self.table_name = "customers"
        #################################
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
        mysql_instance.connect_database()
        mysql_instance.create_database()

    def define_routes(self):
        @self.app.route('/admin_login', methods=['GET', 'POST'])
        def admin_login():
            if request.method == 'POST':
                return self.handle_login_admin()
            return render_template('login_admin.html')

        @self.app.route('/users_accounts/<int:page>', methods=['GET', 'POST'])
        def users_accounts(page=1):
            if 'username' in session:
                return self.list_users_accounts(page=page)
            return redirect(url_for('admin_login'))

        @self.app.route('/login', methods=['GET', 'POST'])
        @self.app.route('/', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                return self.handle_login()
            return render_template('login.html')

        @self.app.route('/register', methods=['GET', 'POST'])
        def register():
            if request.method == 'POST':
                return self.handle_registration()
            return render_template('register.html')



        @self.app.route('/update_customer', methods=['POST'])
        def update_customer():
            return self.handle_update_customer()

        @self.app.route('/delete_customer', methods=['POST'])
        def delete_customer():
            return self.handle_delete_customer()

        @self.app.route('/logout')
        def logout():
            session.clear()
            return redirect(url_for('login'))
        
        @self.app.route('/search_results', methods=['POST'])
        def search_results():
            query = request.form['search_query']  # Get the search query from the form
            users = self.search_users(query)  # Get users matching the query
            # print(users)
            return render_template('search_results.html', users=users)
        
        @self.app.route('/search/suggestions', methods=['GET'])
        def search_suggestions():
            query = request.args.get('q', '')  # Get query parameter
            suggestions = self.get_user_suggestions(query)  # Get user suggestions
            return jsonify(suggestions)

        @self.app.route('/duplicate_users', methods=['GET'])
        def duplicate_user():
            return self.find_users_duplicate()
        @self.app.route('/duplicate_uuids', methods=['GET'])
        def duplicate_uuid():
            return self.find_uuid_duplicate()
        
    def find_uuid_duplicate(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        # Câu lệnh SQL đã được sửa
        cursor.execute(f'SELECT uuid, COUNT(*) FROM {self.table_name} GROUP BY uuid HAVING COUNT(*) > 1')
        duplicate_uuids = cursor.fetchall()
        print("ASfasfasfasf", duplicate_uuids)
        cursor.close()
        conn.close()
        return render_template("duplicate_uuid.html", duplicate_uuids=duplicate_uuids)
    def find_users_duplicate(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        # Câu lệnh SQL đã được sửa
        cursor.execute(f'''
            SELECT username, uuid 
            FROM {self.table_name} 
            WHERE uuid IN (
                SELECT uuid 
                FROM {self.table_name} 
                GROUP BY uuid 
                HAVING COUNT(*) > 1
            )
        ''')
        duplicate_uuids = cursor.fetchall()
        print("ASfasfasfasf", duplicate_uuids)
        cursor.close()
        conn.close()
        return render_template("duplicate_users.html", duplicate_uuids=duplicate_uuids)


    def get_user_suggestions(self, query):
        conn = self.get_db_connection()
        try:
            # cursor = conn.cursor(dictionary=True)
            cursor = conn.cursor()
            cursor.execute(f"SELECT username FROM {self.table_name} WHERE username LIKE %s", (f'%{query}%',))
            suggestions = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Failed to get user suggestions: {e}")
        cursor.close()
        conn.close()
        return suggestions
    def search_users(self, query):
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE username LIKE %s", (f'%{query}%',))
            users = cursor.fetchall()
        except Exception as e:
            print(f"Failed to search users: {e}")
        cursor.close()
        conn.close() 
        return users
    
    def handle_login_admin(self):
        entered_username = request.form.get('username')
        entered_password = request.form.get('password')

        if entered_username == self.valid_username and entered_password == self.valid_password:
            session['username'] = entered_username
            return redirect(url_for('users_accounts', page=1))
        else:
            return render_template('login_admin.html', error="Invalid username or password")

    def handle_login(self):
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'uuid' in request.form:
            username = request.form['username']
            password = request.form['password']
            uuid = request.form['uuid']
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f'SELECT * FROM {self.table_name} WHERE username = %s AND password = %s AND uuid = %s', (username, password, uuid))
            customer = cursor.fetchone()
            cursor.close()
            conn.close()

            if customer:
                session['loggedin'] = True
                session['id'] = customer['id']
                session['username'] = customer['username']
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                msg = f'Logged in successfully/{current_date}/{customer["expdate"]}'
            else:
                msg = 'Incorrect username or password. Please try again.'
        return render_template('login.html', msg=msg)
    


    def handle_registration(self):
        msg = ''
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        uuid = request.form.get('uuid')
        inforuser = request.form.get('inforuser')

        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f'SELECT username FROM {self.table_name} WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            msg = 'Username already exists!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password:
            msg = 'Please fill out the form!'
        else:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d')
            cursor.execute(f'INSERT INTO {self.table_name} (username, password, phone ,address, expdate, uuid, inforuser) VALUES (%s, %s, %s, %s, %s, %s, %s)', (username, password, phone, address, current_time, uuid, inforuser))
            conn.commit()
            msg = 'You have successfully registered!'
        
        cursor.close()
        conn.close()
        
        return render_template('register.html', msg=msg)

    def list_users_accounts(self, page=1):
        per_page = 100  # Số lượng bản ghi mỗi trang
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(f"SELECT COUNT(*) AS total FROM {self.table_name}")
            total = cursor.fetchone()['total']
            offset = (page - 1) * per_page
            cursor.execute(f"SELECT * FROM {self.table_name} LIMIT %s OFFSET %s", (per_page, offset))
            customers = cursor.fetchall()
        except Exception as e:
            print(f"Failed to fetch customers: {e}")
        # print(customers)
        cursor.close()
        conn.close()
        # total_pages = (total - 1) // per_page + 1
        total_pages = (total + per_page - 1) // per_page
        return render_template('users_accounts.html', customers=customers, page=page,  total_pages=total_pages)

    def handle_update_customer(self):
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
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(update_query, (username, password, phone, address, expdate, uuid, inforuser, timesapproval, notes, customer_id))
            conn.commit()
        except Exception as e:
            print(f"Failed to update customer: {e}")
        cursor.close()
        conn.close()    

        return jsonify({'status': 'success'})

    def handle_delete_customer(self):
        customer_id = request.form['id']
        delete_query = "DELETE FROM customers WHERE id = %s"
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(delete_query, (customer_id,))
            conn.commit()
        except Exception as e:
            print(f"Failed to delete customer: {e}")
        cursor.close()
        conn.close()
        return jsonify({'status': 'success'})

    def run(self):
        self.app.run(debug=True)

# Create an instance of MyApp
app_instance = MyApp()
app = app_instance.app

if __name__ == "__main__":
    app_instance.run()
