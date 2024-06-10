from contextlib import contextmanager

@contextmanager
def cursorHandler(connection):
    cursor = connection.cursor()
    yield cursor
    cursor.close()
    connection.commit()

def insert_into_table(cursor, query, values):
    cursor.execute(query, values)

def use_stackOverflowDB(cursor):
    cursor.execute("Use StackOverflow")

def create_db_and_variableTable(cursor):
    cursor.execute("CREATE DATABASE IF NOT EXISTS StackOverflow")
    use_stackOverflowDB(cursor)
    cursor.execute("""Create Table IF NOT EXISTS Variables(
               users_page_no INT,
               last_user_id INT,
               no_of_users INT,
               no_of_users_per_page INT, 
               top_tags_needed INT)""")
    
def create_dataTable(cursor):
    cursor.execute("""CREATE TABLE IF NOT EXISTS UserData(
                   account_id INT, 
                   reputation INT, 
                   user_id INT, 
                   accept_rate INT,
                   link VARCHAR(255),
                   display_name VARCHAR(150), 
                   Bronze_Badge_Count INT, 
                   Silver_Badge_Count INT, 
                   Gold_Badge_Count INT,
                   Tag_Name VARCHAR(100),
                   Answer_Count INT,
                   Answer_Score INT,
                   Question_Count INT,
                   Question_Score INT)""")
    
def create_userIdTable(cursor):
    cursor.execute("Create Table IF NOT EXISTS UserIDS(User_ID INT)")
    
def retrieve_from_table(cursor, query):
    cursor.execute(query)
    return cursor.fetchall()
