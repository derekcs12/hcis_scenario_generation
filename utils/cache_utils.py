from pyexpat import EXPAT_VERSION
import time
import json
import requests
import os

CACHE_FILE = 'runtime_data/itri_cache.json'
CACHE_EXPIRY = 600  # Default cache expiry time in seconds

global cache
# Load cache from file if it exists
def load_cache_from_file():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save cache to file
def save_cache_to_file(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)



def get_from_cache(cache_key):
    """Retrieve data from cache if it exists and is not expired."""
    # print("======>cache_key: ", cache_key)
    current_time = time.time()
    if cache_key in cache:
        cache_entry = cache[cache_key]
        if cache_entry['expires_at'] > current_time:
            return cache_entry['data']
        else:
            # Cache expired
            del cache[cache_key]
            save_cache_to_file(cache)
    return None

def set_to_cache(cache_key, data, ttl=CACHE_EXPIRY):
    """Store data in cache with a time-to-live (TTL)."""
    current_time = time.time()
    cache[cache_key] = {
        'data': data,
        'expires_at': current_time + ttl
    }
    save_cache_to_file(cache)

def get_cache_data(url, headers=None):
    cache_key = f"fetch_data_{url}"
    data_list = get_from_cache(cache_key)
    
    if data_list is None:
        try:
            response = requests.get(url, headers=headers)
            # response.raise_for_status()
            data_list = response.json()  # Assuming the response is JSON
            # print(data_list);exit("DSFDFSDf")
            print("No Cache data, GET")
        except Exception as e:
            print(f"Error fetching data: {e}")
            return False
        
        # Update the cache
        set_to_cache(cache_key, data_list, ttl=300)  # Cache for 300 seconds
    
    return data_list

# Function to clear cache file
def clear_cache_file():
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        
# Global cache dictionary
cache = load_cache_from_file()   
    
    
