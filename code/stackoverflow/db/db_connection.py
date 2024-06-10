from mysql.connector import connect

try:
    connection = connect(host='localhost',
                         user='root',
                         password='password')

except:
    print("Error occured while trying to connect to MySQL")