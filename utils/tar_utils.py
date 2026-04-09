import tarfile
import os

def reset_tarinfo(tarinfo):
    tarinfo.mtime = 0
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = "root"
    tarinfo.gname = "root"
    return tarinfo

def create_tar(source_dir, tar_path):
    with tarfile.open(tar_path, "w") as tar:
        for root, dirs, files in os.walk(source_dir):
            dirs.sort()
            for file in sorted(files):
                full = os.path.join(root, file)
                arcname = os.path.relpath(full, source_dir)
                tar.add(full, arcname=arcname, filter=reset_tarinfo)

def extract_tar(tar_path, dest):
    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(dest)