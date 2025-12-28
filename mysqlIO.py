import mysql.connector
import os


class mysqlIO:
    def __init__(self, host, user, password, database, logger=None):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor(dictionary=True)
        self.logger = logger

    def return_wrapper(self, response):
        if self.logger:
            self.logger.debug(f"MySQL query response: {response}")
        return response

    def query(self, query):
        self.cursor.execute(query)
        return self.return_wrapper(self.cursor.fetchall())

    def close(self):
        self.cursor.close()
        self.connection.close()


if __name__ == "__main__":
    db = mysqlIO("192.168.10.99", os.environ['DB_USER'], os.environ['DB_PASSWORD'], "micrograms")
