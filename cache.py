# cache.py

cache_db = {}

def get_cached(url, quality):
    return cache_db.get(f"{url}_{quality}")

def save_cache(url, quality, file_id):
    cache_db[f"{url}_{quality}"] = file_id
