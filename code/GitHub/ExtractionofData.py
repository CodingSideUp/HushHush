import json
import requests
from urllib.parse import urljoin
import csv
from datetime import datetime
import mysql.connector

# Define the handle_error function
def handle_error(response, username, repo_name, action):
    print(f'Error fetching {action} for {username}/{repo_name}: {response.status_code} - {response.text}')

# MySQL database connection details
db_config = {
    'host': '127.0.0.1',
    'user': ' root',
    'password': 'password',
    'database': 'github_data',
}

access_token = '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'
base_url = 'https://api.github.com'
per_page = 100
headers = {'Authorization': f'token {access_token}'}

# Establish MySQL connection
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Create a table to store the GitHub data
create_table_query = """
CREATE TABLE IF NOT EXISTS github_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Timestamp DATETIME,
    Username VARCHAR(255),
    Followers INT,
    Following INT,
    Repo_name VARCHAR(255),
    Repo_url VARCHAR(255),
    Languages VARCHAR(255),
    Stargazers INT,
    Contributors INT,
    Subscribers INT,
    Pulls INT,
    Commits INT,
    Size INT
);
"""
cursor.execute(create_table_query)

search_endpoint = '/search/users'
url_search = urljoin(base_url, search_endpoint)

params = {
    'q': 'developer OR engineer OR programmer OR software OR IT',  # Empty query retrieves all users
    'type': 'Users',
    'per_page': per_page
}

try:
    response_search = requests.get(url_search, params=params, headers=headers)
    response_search.raise_for_status()
    search_results = response_search.json()

    for user in search_results.get('items', []):
        username = user.get('login')
        user_data = {'username': username, 'repositories': []}

        try:
            user_url = urljoin(base_url, f'/users/{username}')
            response_user = requests.get(user_url, headers=headers)
            response_user.raise_for_status()
            user_info = response_user.json()
            user_data['followers'] = user_info.get('followers', 0)
            user_data['following'] = user_info.get('following', 0) 
            user_repos_endpoint = f'/users/{username}/repos'
            url_repos = urljoin(base_url, user_repos_endpoint)
            response_repos = requests.get(url_repos, params={'per_page': per_page}, headers=headers)

            if response_repos.status_code == 200:
                repos_data = response_repos.json()

                for repo in repos_data:
                    repo_data = {'name': repo['name'], 'url': repo['html_url']}

                    repo_languages_url = urljoin(base_url, f'/repos/{username}/{repo["name"]}/languages')
                    response_languages = requests.get(repo_languages_url, headers=headers)

                    if response_languages.status_code == 200:
                        languages_data = response_languages.json()
                        repo_data['languages'] = languages_data
                    else:
                        repo_data['languages'] = []
                        handle_error(response_languages, username, repo['name'], 'languages')

                    repo_stargazers_url = urljoin(base_url, f'/repos/{username}/{repo["name"]}/stargazers')
                    response_stargazers = requests.get(repo_stargazers_url, headers=headers)

                    if response_stargazers.status_code == 200:
                        stargazers_data = response_stargazers.json()
                        repo_data['stargazers'] = stargazers_data
                    else:
                        repo_data['stargazers'] = []
                        handle_error(response_stargazers, username, repo['name'], 'stargazers')

                    repo_contributors_url = urljoin(base_url, f'/repos/{username}/{repo["name"]}/contributors')
                    response_contributors = requests.get(repo_contributors_url, headers=headers)

                    if response_contributors.status_code == 200:
                        contributors_data = response_contributors.json()

                        user_contributors = [
                            contributor['login'] for contributor in contributors_data
                            if contributor['login'] == username
                        ]

                        repo_data['contributors'] = contributors_data
                    else:
                        repo_data['contributors'] = []
                        handle_error(response_contributors, username, repo['name'], 'contributors')

                    repo_subscribers_url = urljoin(base_url, f'/repos/{username}/{repo["name"]}/subscribers')
                    response_subscribers = requests.get(repo_subscribers_url, headers=headers)

                    if response_subscribers.status_code == 200:
                        subscribers_data = response_subscribers.json()
                        repo_data['subscribers'] = subscribers_data
                    else:
                        repo_data['subscribers'] = []
                        handle_error(response_subscribers, username, repo['name'], 'subscribers')

                    repo_pulls_url = urljoin(base_url, f'/repos/{username}/{repo["name"]}/pulls')
                    response_pulls = requests.get(repo_pulls_url, headers=headers)

                    if response_pulls.status_code == 200:
                        pulls_data = response_pulls.json()
                        repo_data['pulls'] = pulls_data
                    else:
                        repo_data['pulls'] = []
                        handle_error(response_pulls, username, repo['name'], 'pulls')

                    repo_commits_url = urljoin(base_url, f'/repos/{username}/{repo["name"]}/commits')
                    response_commits = requests.get(repo_commits_url, headers=headers)

                    if response_commits.status_code == 200:
                        commits_data = response_commits.json()

                        user_commits = [
                            commit for commit in commits_data
                            if 'author' in commit and commit['author'] and 'login' in commit['author'] and commit['author']['login'] == username
                        ]

                        repo_data['commits'] = user_commits
                    else:
                        repo_data['commits'] = []
                        handle_error(response_commits, username, repo['name'], 'commits')

                    repo_size_url = urljoin(base_url, f'/repos/{username}/{repo["name"]}')
                    response_size = requests.get(repo_size_url, headers=headers)

                    if response_size.status_code == 200:
                        size_data = response_size.json()
                        repo_data['size'] = size_data.get('size', 0)
                    else:
                        repo_data['size'] = 0
                        handle_error(response_size, username, repo['name'], 'size')

                    # Insert data into MySQL
                    insert_query = """
                    INSERT INTO github_data 
                    (Timestamp, Username, Followers, Following, Repo_name, Repo_url, Languages, Stargazers, Contributors, Subscribers, Pulls, Commits, Size) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """
                    data = (
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        username,
                        user_data['followers'],
                        user_data['following'],
                        repo_data['name'],
                        repo['html_url'],
                        ', '.join(languages_data.keys()),
                        len(repo_data['stargazers']),
                        len(repo_data['contributors']),
                        len(repo_data['subscribers']),
                        len(repo_data['pulls']),
                        len(repo_data['commits']),
                        repo_data['size']
                    )

                    try:
                        cursor.execute(insert_query, data)
                        conn.commit()
                    except mysql.connector.Error as e:
                        print(f"Error inserting data into MySQL: {e}")

                    user_data['repositories'].append(repo_data)

            else:
                user_data['repositories'] = []
                handle_error(response_repos, username, '', 'repositories')

        except requests.exceptions.RequestException as user_request_error:
            print(f'Error fetching user information for {username}: {user_request_error}')

except requests.exceptions.RequestException as search_request_error:
    print(f'Error fetching user information: {search_request_error}')

# Close MySQL connection
cursor.close()
conn.close()
