import mysql.connector
import os


class mysqlIO:
    def __init__(self, host, user, password, database):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor(dictionary=True)

    def query(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.connection.close()


if __name__ == "__main__":
    db = mysqlIO("192.168.10.99", os.environ['DB_USER'], os.environ['DB_PASSWORD'], "micrograms")
