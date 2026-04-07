import tempfile, shutil, os
from utils.tar_utils import create_tar
from utils.hashing import sha256_file
from utils.paths import LAYERS_DIR

def create_layer(fs_path):
    tar_path = tempfile.mktemp(suffix=".tar")
    create_tar(fs_path, tar_path)

    digest = sha256_file(tar_path)
    final_path = os.path.join(LAYERS_DIR, digest + ".tar")

    shutil.move(tar_path, final_path)
    return digest