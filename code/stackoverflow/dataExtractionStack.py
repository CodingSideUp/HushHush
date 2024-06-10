# Code for Data Extraction in a synchronous manner, will try to update the code by using asyncio or threading

# import statements
import time
import math
import warnings
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)
import pandas as pd
import requests
import numpy as np

from db.stackoverflow_db import create_dataTable, create_db_and_variableTable, create_userIdTable, cursorHandler, insert_into_table,retrieve_from_table, use_stackOverflowDB
from db.db_connection import connection

current_time = time.time()

# Getting the previously stored variables if present or else initialising the variables with necessary values
try:
    with cursorHandler(connection) as cursor:
        use_stackOverflowDB(cursor)
        values = retrieve_from_table(cursor, "Select * from Variables")[0]
    users_page_no = values[0]
    last_user_id = values[1]
    no_of_users = values[2]
    no_of_users_per_page = values[3]
    top_tags_needed = values[4]

except:
    with cursorHandler(connection) as cursor:
        create_db_and_variableTable(cursor)
    users_page_no = 1
    last_user_id = 0
    no_of_users = 300
    no_of_users_per_page = 100
    top_tags_needed = 10

try:
    with cursorHandler(connection) as cursor:
        user_ids = [id[0] for id in retrieve_from_table(cursor, "Select * from UserIDS")]
except:
    with cursorHandler(connection) as cursor:
        create_userIdTable(cursor)
    user_ids = []

try:
    with cursorHandler(connection) as cursor:
        data = retrieve_from_table(cursor, """Select userdata.* from userdata Inner Join userids On userdata.user_id = userids.user_id;""")
        old_users = [dict(zip([i[0] for i in cursor.description][:-5], j[:-5])) for j in data]
        tags = [dict(zip([i[0] for i in cursor.description][-5:], j[-5:])) for j in data]
        
        column_rename_dict = {"Bronze_Badge_Count" : "bronze",
                              "Silver_Badge_Count" : "silver",
                              "Gold_Badge_Count" : "gold"}
        for user in old_users:
            user['badge_counts'] = {values[1] : user[values[0]] for values in column_rename_dict.items()}
            for names in column_rename_dict.items():
                user.pop(names[0])

        output_users = np.asarray([{**i, "tags": j} for i, j in zip(old_users, tags)])
except:
    with cursorHandler(connection) as cursor:
        create_dataTable(cursor)
    output_users = np.array([])

users_to_dlt = []

# Function to extract a list of users from Stack Overflow
def extraction_of_users(users_page_no, output_users, user_ids,no_of_pages, no_of_users_per_page):
    a = time.time()
    for i in range(users_page_no, users_page_no + no_of_pages):
        response = requests.get(f"https://api.stackexchange.com/2.3/users?page={i}&pagesize={no_of_users_per_page}&order=desc&sort=reputation&site=stackoverflow").json()
        
        output_users = np.append(output_users, response['items'])
        user_ids.extend([user['user_id'] for user in response['items']])

        if "backoff" in response.keys():
            print("User loop : ", response['backoff'])
            time.sleep(response['backoff'])

        if response["quota_remaining"] == 1:
            print("Quota over while fetching users")
            users_page_no = i + 1
            return output_users, user_ids, users_page_no

    users_page_no = i + 1
    print("Time Taken : ", time.time() - a)
    return output_users, user_ids, users_page_no

# Function to extract the top 'n' tags of a user in Stack Overflow
def tags_per_user(user_ids, last_user_id, output_users, page_no, pagesize):
    for user in output_users:
        a = time.time()
        response = requests.get(f"https://api.stackexchange.com/2.3/users/{user['user_id']}/top-tags?page={page_no}&pagesize={pagesize}&site=stackoverflow").json()

        user.update({"tags" : response['items']})
        user_ids.remove(user['user_id'])
        users_to_dlt.append(user['user_id'])
        
        if response["quota_remaining"] <= 1:
            "quota_remaining"
            print(f'Quota over while fetching the top tags of user_id : {user["user_id"]}')
            last_user_id = user['user_id']
            return output_users, user_ids, last_user_id

        if "backoff" in response.keys():
            print("Tag loops : ", response['backoff'])
            time.sleep(response['backoff'])

        print("Tag Time Taken : ", time.time() - a)
    last_user_id = user['user_id']
    return output_users, user_ids, last_user_id

# Function to preprocess the extracted JSON Data
def preprocess(output_users):
    df = pd.json_normalize(output_users)
    columns_to_drop = ['collectives', 'is_employee', 'last_modified_date', 'last_access_date', 'reputation_change_year', 'reputation_change_quarter', 'reputation_change_month', 'reputation_change_week', 'reputation_change_day', 'creation_date', 'user_type', 'location', 'website_url', 'profile_image']
    df.drop(columns=columns_to_drop, inplace = True, axis = 1)
    df.fillna({'accept_rate' : 0}, inplace = True)
    return df

# Function call for extraction_of_users
if len(user_ids) < 300:
    print(output_users)
    output_users, user_ids, users_page_no = extraction_of_users(output_users = output_users, user_ids = user_ids, users_page_no = users_page_no, no_of_pages = math.ceil(no_of_users/no_of_users_per_page), no_of_users_per_page = no_of_users_per_page)
    print(len(output_users))

# Function call for tags_per_user
output_users, user_ids, last_user_id = tags_per_user(last_user_id = last_user_id, output_users = output_users, user_ids = user_ids, page_no = 1, pagesize = top_tags_needed)

# Function call to get processed data
df = preprocess(output_users)

# Storing the variables and the data in the respective tables
with cursorHandler(connection) as cursor:
    a = time.time()
    try:
        if values:
            insert_into_table(cursor, "Update Variables Set users_page_no = %s, last_user_id = %s, no_of_users = %s, no_of_users_per_page = %s, top_tags_needed = %s", (users_page_no, last_user_id, no_of_users, no_of_users_per_page, top_tags_needed))
    except:
        insert_into_table(cursor, "Insert into Variables Values(%s, %s, %s, %s, %s)", (users_page_no, last_user_id, no_of_users, no_of_users_per_page, top_tags_needed))

    print("Var time :", time.time() - a)

with cursorHandler(connection) as cursor:
    a = time.time()
    cursor.execute("DELETE FROM userids;")
    insert_into_table(cursor, "Insert into userids values " + ', '.join(['(%s)' for i in range(len(user_ids))]), tuple(user_ids))
    print("UserIDS time :", time.time() - a)

with cursorHandler(connection) as cursor:
    a = time.time()
    cursor.execute("Delete from userdata where user_id in" + str(tuple(users_to_dlt)))
    for index, row in df.iterrows():
        if type(row.iloc[6]) is list:
            for i in row.iloc[6]:
                insert_into_table(cursor, "Insert Into UserData Values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (row.iloc[0], row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4], row.iloc[5], row.iloc[7], row.iloc[8], row.iloc[9], i['tag_name'], i['answer_count'], i['answer_score'], i['question_count'], i['question_score']))
        else:
            insert_into_table(cursor, "Insert Into UserData Values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (row.iloc[0], row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4], row.iloc[5], row.iloc[7], row.iloc[8], row.iloc[9], 'Have to fetch', 0, 0, 0, 0))
    print("Data time :", time.time() - a)

connection.close()
print("Time taken `to run the code :", time.time() - current_time, "s")