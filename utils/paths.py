import os

DOCKSMITH_DIR = os.path.expanduser("~/.docksmith")
LAYERS_DIR = os.path.join(DOCKSMITH_DIR, "layers")
IMAGES_DIR = os.path.join(DOCKSMITH_DIR, "images")
CACHE_DIR = os.path.join(DOCKSMITH_DIR, "cache")

def init_dirs():
    os.makedirs(LAYERS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)