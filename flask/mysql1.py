import mysql.connector
from threading import Thread

class mysql_data:
    def __init__(self, host=None, user=None, password=None, database=None, table=None):
        self.host = host
        self.user_host = user
        self.password_host = password
        self.database = database
        self.table = table
       
    def create_database(self):
        connect = mysql.connector.connect(host=self.host, user=self.user_host, password=self.password_host)
        cursor = connect.cursor()
        cursor.execute(f'CREATE DATABASE IF NOT EXISTS {self.database}')
        cursor.execute(f'USE {self.database}')
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.table}(
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            passport VARCHAR(255) NOT NULL,
            expdate VARCHAR(255))
            """)
        connect.commit()
        cursor.close()


# host = "localhost"
# user = "root"
# password = "123456"
# database_name = "user_data"
# table_name = "customers"

# mysql_instance = mysql_data(host, user, password, database_name, table_name)
# Thread(target=mysql_instance.create_database).start()