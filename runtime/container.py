import os, json, tempfile, shutil, subprocess
from utils.paths import IMAGES_DIR, LAYERS_DIR
from utils.tar_utils import extract_tar
from runtime.isolation import isolate_and_run

def run_container(tag, cmd_override=None, env_override={}):
    path = os.path.join(IMAGES_DIR, tag.replace(":", "_") + ".json")

    if not os.path.exists(path):
        print("Image not found")
        return

    with open(path) as f:
        manifest = json.load(f)

    root = tempfile.mkdtemp()

    
    for layer in manifest["layers"]:
        extract_tar(os.path.join(LAYERS_DIR, layer + ".tar"), root)

    
    cmd = cmd_override if cmd_override else manifest["config"]["Cmd"]

    
    if cmd[0] == "python3":
        cmd[0] = "/usr/bin/python3"

    workdir = manifest["config"]["WorkingDir"]

   
    env = {}
    env["PATH"] = "/usr/bin:/bin"
    env["PYTHONHOME"] = "/usr"

    for e in manifest["config"]["Env"]:
        k, v = e.split("=")
        env[k] = v

    env.update(env_override)

 
    os.makedirs(os.path.join(root, "usr/bin"), exist_ok=True)

    
    shutil.copy("/usr/bin/python3", os.path.join(root, "usr/bin/python3"))

    
    loader_path = "/lib64/ld-linux-x86-64.so.2"
    if os.path.exists(loader_path):
        dest = os.path.join(root, loader_path.lstrip("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy(loader_path, dest)

    
    ldd_output = subprocess.check_output(["ldd", "/usr/bin/python3"]).decode()

    for line in ldd_output.split("\n"):
        line = line.strip()
        if "=>" in line:
            parts = line.split("=>")
            lib_path = parts[1].strip().split(" ")[0]

            if os.path.exists(lib_path):
                dest_path = os.path.join(root, lib_path.lstrip("/"))
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy(lib_path, dest_path)

    
    python_lib_src = "/usr/lib/python3.10"
    python_lib_dest = os.path.join(root, "usr/lib/python3.10")

    shutil.copytree(python_lib_src, python_lib_dest, dirs_exist_ok=True)

    
    isolate_and_run(root, cmd, env, workdir)

    
    shutil.rmtree(root)