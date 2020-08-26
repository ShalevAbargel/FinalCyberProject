import mysql.connector
from mysql.connector import Error


class MyDB(object):

    def __init__(self, host=None):
        """
        This function initializes the http request handler with parameters
        :param ip:String. the ip where mysql server is open, if None then ip = localhost
        """
        if host:
            self._host = host
        else:
            self._ip = 'db4free.net'
        self._password = 'adminadmin'
        self._username = 'shalevaviad'
        self._database = 'platformsdb'
        self.connection = None
        self.crusor = None

    def connect(self):
        """
        This function connect to database
        """
        try:
            self.connection = mysql.connector.connect(host=self._ip,
                                                      database=self._database,
                                                      user=self._username,
                                                      password=self._password)
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print("Connected to MySQL Server version ", db_info)
                self.cursor = self.connection.cursor()
                self.cursor.execute("select database();")
                record = self.cursor.fetchone()
                print("You're connected to database: ", record)
        except Error as e:
            print("Error while connecting to MySQL", e)

    def insert_data(self, domain, platform, version):
        """
        This function insert data to table 'platforms' in db
        :param domain: insert domain to column domain
        :param platform: insert platform to column platform
        :param version: insert version to column version
        """
        try:
            mysql_insert_query = """INSERT INTO platforms (domain, platform, version) 
                                    VALUES (%s, %s, %s) """
            record_tuple = (domain, platform, version)
            self.cursor.execute(mysql_insert_query, record_tuple)
            self.connection.commit()
            print(self.cursor.rowcount, "Record inserted successfully into platforms table")
        except mysql.connector.Error as error:
            print("Failed to insert into MySQL table {}".format(error))

    def select(self, domain):
        """
        This function select all rows in table where domain=domain
        :param domain: select all rows in table where domain = domain
        :return: list of all rows where domain=domain
        """
        try:
            sql_select_query = """select * from platforms where domain = %s"""
            self.cursor.execute(sql_select_query, (domain,))
            record = self.cursor.fetchall()
            return record
        except mysql.connector.Error as error:
            print("Failed to get record from MySQL table: {}".format(error))

    def delete(self, domain):
        """
        This function delete all rows in table where domain=domain
        :param domain: delete all rows in table where domain = domain
        """
        try:
            sql_delete_query = """Delete from platforms where domain = %s"""
            self.cursor.execute(sql_delete_query, (domain,))
            self.connection.commit()
            print("Record Deleted successfully ")
        except mysql.connector.Error as error:
            print("Failed to Delete record from table: {}".format(error))

    def disconnect(self):
        """
        This function disconnect from database
        """
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("MySQL connection is closed")
