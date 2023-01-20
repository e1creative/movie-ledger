"""Handle connecting to our external api!"""

import os
import requests

# from keys import API_KEY
API_KEY = os.environ.get('API_KEY')

print("\n***********")
print("API KEY: ", API_KEY)
print("***********\n")

API_BASE_URL = f"http://www.omdbapi.com/?apikey={API_KEY}&"

def movie_search(search_term):
    """Make the external search call to the omdb movie database!"""
    
    api_url = f"{API_BASE_URL}s={search_term}&type=movie"
    
    api_resp = requests.get(api_url)

    # the api returns a reponse with json
    # but we need to convert to a python dictionary
    results = api_resp.json()

    # import pdb
    # pdb.set_trace()

    return results


def movie_search_by_id(movie_id):
    """Make request to the external db from the """

    api_url = f"{API_BASE_URL}i={movie_id}"
    
    api_resp = requests.get(api_url)

    # the api returns a reponse with json
    # but we need to convert to a python dictionary
    results = api_resp.json()

    return results

