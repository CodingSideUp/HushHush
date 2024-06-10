# Import Libraries
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns 
import pickle


from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score


import warnings
warnings.filterwarnings("ignore")


# Variable initialization
features = ['Stargazers','Contributors', 'Subscribers', 'Pulls', 'Commits', 'Size', 'Followers','Following']

user = "root"
password = "password"
host = "localhost"
db_name = "github"

engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{db_name}')

# Created function to find optimum number of clusters
def optimise_k_means(data, max_k):
    k_values = []
    inertias = []
    
    for k in range(1, max_k):
        kmeans = KMeans(n_clusters=k)
        kmeans.fit(data)
        
        k_values.append(k)
        inertias.append(kmeans.inertia_)
    
    # Generate the elbow plot
    fig = plt.subplots(figsize=(10,5))
    plt.plot(k_values, inertias, 'o-')
    plt.xlabel('Number of Clusters')
    plt.ylabel('WCSS')
    plt.grid(True)
    plt.show()

    
def train_test_kmeans(data):
    # Initialize KMeans model
    kmeans = KMeans(n_clusters=9, random_state=42)
    kmeans.fit(data)
    
    # Predict clusters on the data
    clusters = kmeans.predict(data)
    cluster_labels = kmeans.labels_
    
    # Compute silhouette score (a measure of how well-defined the clusters are)
    silhouette_avg = silhouette_score(data, clusters)
    print(f"Silhouette Score: {silhouette_avg}")
    
    with open('model_kmean.pkl', 'wb') as f:
        pickle.dump(clusters, f)
    
    return kmeans, clusters, cluster_labels

# Retrieving the data from the database
df = pd.read_sql(sql="select * from userdata where Tag_Name != 'Have to fetch'", con=engine)

#Preprocessing the data
current_dir = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(current_dir, 'pickel file\\scaler.pkl'), 'rb') as scaler_file:
        scaler = pickle.load(scaler_file)
        df[features] = scaler.transform(df[features])
except:
    scaler = StandardScaler()
    df[features] = scaler.fit_transform(df[features])
    with open(os.path.join(current_dir, 'pickel file\\scaler.pkl'), 'wb') as scaler_file:
        pickle.dump(scaler, scaler_file)


optimise_k_means(df[features],50) #10is the max numbers of clusters it will create and identify the best K number.
kmeans, clusters, cluster_labels = train_test_kmeans(df[features])

# Creating a new column
df['kmean_n'] = cluster_labels

# Cluster analysis
# features = ['Stargazers','Contributors', 'Subscribers', 'Pulls', 'Commits', 'Size', 'Followers','Following', 'kmeans_N']
# for cluster_user_values in git_df[git_df['kmeans_N'] == 9][features].values:
#     for trainingData_thirdQuartileValue, cluster_user_value, feature in zip(git_df.describe()[features].loc['75%'], cluster_user_values, features):
#         print(f'{feature} : 75% -> {trainingData_thirdQuartileValue}, {cluster_user_value}')
#     print()


# Labelling the data 1 or 0
labels = []
chosen_clusters = (1, 3, 4, 6, 9)
df['labels'] = df['kmeans_n'].apply(lambda j: 1 if j in chosen_clusters else 0)

# for j in git_df['kmeans_n']:
#     if j in chosen_clusters:
#         labels.append(1)
#     else:
#         labels.append(0)
        
# Inserting the labelleddata into the database
df.to_sql('labelled_data', con=engine, if_exists='replace', index=False)
engine.dispose() 

