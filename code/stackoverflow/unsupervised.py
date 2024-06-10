from sqlalchemy import create_engine
import os

import warnings
warnings.filterwarnings("ignore", "\nPyarrow", DeprecationWarning)

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
import pickle

# Variable initialization
current_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(current_dir, 'pickle_files/kmeans_model.pkl')
scaler_filename = os.path.join(current_dir, "pickle_files/standardScaler.pkl")
features = ['reputation', 'accept_rate', 'Bronze_Badge_Count', 'Silver_Badge_Count', 'Gold_Badge_Count', 'Answer_Count', 'Answer_Score', 'Question_Count', 'Question_Score']

user = "root"
password = "password"
host = "localhost"
db_name = "stackoverflow"

engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{db_name}')

# Function to find out the optimal K value
def optimal_k_value(df, max_k_value):
    wcss = []
    silhouette_scores = []
    
    for k in range(2, max_k_value):
        kmeans = KMeans(n_clusters=k, random_state = 5)
        kmeans.fit(df)
        
        wcss.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(df, kmeans.predict(df)))
        print(f'The silhouette score for {k} clusters is {silhouette_scores[k-2]}')
        
    # To Generate the elbow plot
    fig = plt.subplots(figsize=(10, 10))
    plt.plot(range(2, max_k_value), wcss,'o-')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Inertia')
    plt.grid(True)
    plt.show()

    return silhouette_scores

# Function to do the K-Means Clustering
def k_means_clustering(df):
    silhouette_scores = optimal_k_value(df[features], 50)    

    #print(silhouette_scores)

    # After looking at the Elbow Plot and the Silhoutte Scores, the optimal number of clusters are chosen, which is 8 in this case
    cluster = KMeans(n_clusters= 8, random_state=5)
    cluster.fit(train_data[features])

    with open(filename, 'wb') as f:
        pickle.dump(cluster, f)
    return cluster

# Retrieving the data from the database
df = pd.read_sql(sql="select * from userdata where Tag_Name != 'Have to fetch'", con=engine)

#Preprocessing the data
try:
    with open(scaler_filename, 'rb') as f:
        scaler = pickle.load(f)
    df[features] = scaler.transform(df[features])
except:
    scaler = StandardScaler()
    df[features] = scaler.fit_transform(df[features])
    with open(scaler_filename, 'wb') as f:
        pickle.dump(scaler, f)   

# Labelling the data
chosen_clusters = (1, 2, 4, 5, 7)
try:
    with open(filename, 'rb') as f:
        cluster = pickle.load(f)
    print("File present")
    df['label'] = [1 if label in chosen_clusters else 0 for label in cluster.predict(df[features])]

except:
    print("File not present")
    train_data = df.sample(1000, random_state=5)
    cluster = k_means_clustering(train_data)
    df['label'] = [1 if label in chosen_clusters else 0 for label in cluster.predict(df[features])]

# Inserting the labelleddata into the database
df.to_sql('labelleddata', con=engine, if_exists='replace', index=False)
engine.dispose()     

# Manually choosing the user of a particular cluster is selected or not
## Change the numerical value in the first for loop and manually understand how the clustering has been done, comparing the values of the features of the user in every cluster with the 3rd quartile value of that feature in the training data

# for cluster_user_values in train_data[train_data['label'] == 3][features].values:
#     for trainingData_thirdQuartileValue, cluster_user_value, feature in zip(train_data.describe()[features].loc['75%'], cluster_user_values, features):
#         print(f'{feature} : 75% -> {trainingData_thirdQuartileValue}, {cluster_user_value}')
#     print()