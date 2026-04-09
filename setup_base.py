import os
import urllib.request
import tempfile
import tarfile
import json
import shutil
import time
from builder.layers import create_layer
from utils.paths import init_dirs, IMAGES_DIR, LAYERS_DIR

ALPINE_URL = "https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/x86_64/alpine-minirootfs-3.18.5-x86_64.tar.gz"

def setup_base():
    init_dirs()
    print(f"Downloading base image from {ALPINE_URL}...")
    
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tf:
        urllib.request.urlretrieve(ALPINE_URL, tf.name)
        archive_path = tf.name

    print("Extracting archive...")
    extract_dir = tempfile.mkdtemp()
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(extract_dir)

    print("Creating layer from extracted rootfs...")
    # This will use the consistent tar creation to give it our deterministic digest
    digest = create_layer(extract_dir)
    print(f"Base layer digest: {digest}")

    manifest = {
        "name": "alpine",
        "tag": "3.18",
        "layers": [digest],
        "created": int(time.time()),
        "config": {
            "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
            "Cmd": ["/bin/sh"],
            "WorkingDir": "/"
        }
    }

    manifest_path = os.path.join(IMAGES_DIR, "alpine_3.18.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    os.remove(archive_path)
    shutil.rmtree(extract_dir)
    print("Setup complete. You can now use FROM alpine:3.18 in your Docksmithfile.")

if __name__ == "__main__":
    setup_base()
