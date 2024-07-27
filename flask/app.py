from threading import Thread
import mysql.connector
import os
import json
import requests
import telebot
import re
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from mysql1 import mysql_data

def send_mess_tele(token: str, group_id: str, content: str):
    try:
        print(f"Telegram Token: {token}")
        print(f"Telegram Group ID: {group_id}")
        bot = telebot.TeleBot(token=token)
        bot.send_message(chat_id=group_id, text=content)
    except Exception as e:
        print(f"Failed to send message: {e}")

def get_time():
    response = requests.get("http://worldtimeapi.org/api/timezone/Asia/Ho_Chi_Minh")
    data = response.json()
    current_time_str = data['datetime']
    current_time = datetime.datetime.fromisoformat(current_time_str)
    return current_time

class MyApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.list_token = '6974585517:AAFXdPKmyb050h1vm_HLYndFd8rBQyU4vwI'
        self.group_id = "-4214402614"

        self.valid_username = "nhothoang"
        self.valid_password = "km@123456"
        self.app.secret_key = 'nhothoang'

        self.host = "localhost"
        self.user = "root"
        self.password = "123456"
        self.database_name = "user_data"
        self.table_name = "customers"

        self.create_database()
        self.define_routes()

    def create_database(self):
        mysql_instance = mysql_data(self.host, self.user, self.password, self.database_name, self.table_name)
        Thread(target=mysql_instance.create_database).start()

    def get_db_connection(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database_name
        )

    def define_routes(self):
        @self.app.route('/check')
        def index():
            if 'username' in session:
                return redirect(url_for('expdate'))
            return render_template('login1.html')

        @self.app.route('/login1', methods=['POST'])
        def login1():
            entered_username = request.form.get('username')
            entered_password = request.form.get('password')

            if entered_username == self.valid_username and entered_password == self.valid_password:
                session['username'] = entered_username
                return redirect(url_for('expdate'))
            else:
                return render_template('login1.html', error="Invalid username or password")

        @self.app.route('/login', methods=['GET', 'POST'])
        @self.app.route('/', methods=['GET', 'POST'])
        def login():
            msg = ''
            if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
                username = request.form['username']
                password = request.form['password']
                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f'SELECT * FROM {self.table_name} WHERE username = %s AND password = %s', (username, password))
                customer = cursor.fetchone()
                if customer:
                    session['loggedin'] = True
                    session['id'] = customer['id']
                    session['username'] = customer['username']
                    msg = f'Logged in successfully! {customer["expdate"]}'
                else:
                    msg = 'Incorrect username or password. Please try again.'
                cursor.close()
                conn.close()
            return render_template('login.html', msg=msg)

        @self.app.route('/register', methods=['GET', 'POST'])
        def register():
            msg = '' 
            if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'passport' in request.form:
                username = request.form['username']
                password = request.form['password']
                passport = request.form['passport']
                conn = self.get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f'SELECT * FROM {self.table_name} WHERE username = %s OR passport = %s', (username, passport))
                existing_user = cursor.fetchone()
                if existing_user:
                    if existing_user['username'] == username:
                        msg = 'Username already exists!'
                    elif existing_user['passport'] == passport:
                        msg = 'Passport already exists!'
                elif not re.match(r'[A-Za-z0-9]+', username):
                    msg = 'Username must contain only characters and numbers!'
                elif not username or not password:
                    msg = 'Please fill out the form!'
                else:
                    current_time = get_time()
                    cursor.execute(f'INSERT INTO {self.table_name} (username, password, expdate, passport) VALUES (%s, %s, %s, %s)', (username, password, current_time, passport))
                    conn.commit()
                    msg = 'You have successfully registered!'
                    # send_mess_tele(self.list_token, self.group_id, f"Register success\nAccount: {username}\nPassword: {password}")
                cursor.close()
                conn.close()
            elif request.method == 'POST':
                msg = 'Please fill out the form!'
            return render_template('register.html', msg=msg)

        @self.app.route('/expdate', methods=['GET', 'POST'])
        def approval():
            print("expdate")
            if 'username' in session:
                msg = ''
                if request.method == 'POST' and "username" in request.form and "expdate" in request.form:
                    username = request.form['username']
                    expdate = request.form['expdate']

                    current_time = get_time()
                    print(current_time, expdate)
                    future_time = current_time + datetime.timedelta(days=int(expdate))
                    print(future_time)
                    # try:
                    conn = self.get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(f"SELECT * FROM {self.table_name} WHERE username = %s", (username,))
                    customer = cursor.fetchone()
                    if customer:
                        msg = 'Approval successfully!'
                        cursor.execute(f"UPDATE {self.table_name} SET {'expdate'} = %s WHERE username = %s", (future_time, username))
                        conn.commit()
                    else:
                        msg = 'Incorrect username. Please try again.'
                    cursor.close()
                    conn.close()
                    # except mysql.connector.Error as err:
                    #     msg = f"Error: {err}"
                    # finally:
                    #     cursor.close()
                    #     conn.close()
                return render_template('approval.html', msg=msg, column_name='expdate')
            else:
                return redirect(url_for('index'))

        @self.app.route('/logout')
        def logout():
            session.pop('loggedin', None)
            session.pop('id', None)
            session.pop('username', None)
            return redirect(url_for('login'))

        @self.app.route('/logout2')
        def logout2():
            session.pop('username', None)
            return redirect(url_for('index'))

    def run(self):
        self.app.run(debug=True)

# Create an instance of MyApp
app_instance = MyApp()

# Export the Flask app for Gunicorn
app = app_instance.app

if __name__ == "__main__":
    app_instance.run()
