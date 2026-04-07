import tarfile
import os

def create_tar(source_dir, tar_path):
    with tarfile.open(tar_path, "w") as tar:
        for root, _, files in os.walk(source_dir):
            for file in sorted(files):
                full = os.path.join(root, file)
                arcname = os.path.relpath(full, source_dir)
                tar.add(full, arcname=arcname)

def extract_tar(tar_path, dest):
    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(dest)