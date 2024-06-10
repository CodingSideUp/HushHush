import json
import requests
from urllib.parse import urljoin
import csv
from datetime import datetime

access_token = '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'
base_url = 'https://api.github.com'
roles = ['Data Analyst', 'Data Scientist', 'Data Engineer', 'Machine Learning Engineer']
per_page = 100
headers = {'Authorization': f'token {access_token}'}
result_data = {}

def handle_error(response, username, repo_name, action):
    print(f'Error fetching {action} for {username}/{repo_name}: {response.status_code} - {response.text}')


with open('output.csv', 'w', newline='', encoding='utf-8') as csv_file:
    
    csv_writer = csv.writer(csv_file)

    
    csv_writer.writerow(['Timestamp', 'Role', 'Username', 'Followers', 'Following', 'Repo Name', 'Repo URL', 'Languages', 'Stargazers', 'Contributors', 'Subscribers', 'Pulls', 'Commits', 'Size'])

    for role in roles:
        
        role_data = []

        search_endpoint = '/search/users'
        url_search = urljoin(base_url, search_endpoint)

        params = {
            'q': f'{role}',  
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

                            
                            csv_writer.writerow([
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                                role,
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
                            ])

                            user_data['repositories'].append(repo_data)

                        role_data.append(user_data)

                    else:
                        user_data['repositories'] = []
                        handle_error(response_repos, username, '', 'repositories')

                except requests.exceptions.RequestException as user_request_error:
                    print(f'Error fetching user information for {username}: {user_request_error}')

            result_data[role] = role_data

        except requests.exceptions.RequestException as search_request_error:
            print(f'Error for {role}: {search_request_error}')


with open('output.json', 'w') as json_file:
    json.dump(result_data, json_file, indent=2)


