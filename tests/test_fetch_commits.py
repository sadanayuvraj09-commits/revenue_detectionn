import requests

url = "http://127.0.0.1:8000/fetch_commits"
params = {
    "repo_owner": "sadanayuvraj09-commits",
    "repo_name": "revenue_detective_test"
}

response = requests.post(url, params=params)
print(response.json())
