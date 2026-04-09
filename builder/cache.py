import os
from utils.hashing import sha256_bytes, sha256_file
from utils.paths import CACHE_DIR

def compute_cache_key(prev_digest, instruction, workdir, env):
    env_string = "".join(f"{k}={v}" for k, v in sorted(env.items()))
    data = prev_digest + instruction + workdir + env_string
    return sha256_bytes(data.encode())

def check_cache(key):
    path = os.path.join(CACHE_DIR, key)
    if os.path.exists(path):
        return open(path).read().strip()
    return None

def store_cache(key, digest):
    path = os.path.join(CACHE_DIR, key)
    with open(path, "w") as f:
        f.write(digest)


def hash_directory(path):
    hashes = []

    for root, dirs, files in os.walk(path):
        for f in sorted(files):
            full_path = os.path.join(root, f)
            try:
                hashes.append(sha256_file(full_path))
            except:
                continue

    return "".join(hashes)