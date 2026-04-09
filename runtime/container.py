import os, json, tempfile, shutil, sys
from utils.paths import IMAGES_DIR, LAYERS_DIR
from utils.tar_utils import extract_tar
from runtime.isolation import isolate_and_run

def run_container(tag, cmd_override=None, env_override={}):
    path = os.path.join(IMAGES_DIR, tag.replace(":", "_") + ".json")

    if not os.path.exists(path):
        print("Image not found")
        sys.exit(1)

    with open(path) as f:
        manifest = json.load(f)

    root = tempfile.mkdtemp()

    for layer in manifest.get("layers", []):
        extract_tar(os.path.join(LAYERS_DIR, layer + ".tar"), root)

    cmd = cmd_override if cmd_override else manifest["config"]["Cmd"]
    workdir = manifest["config"].get("WorkingDir", "/")

    env = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin"}
    
    for e in manifest["config"].get("Env", []):
        if "=" in e:
            k, v = e.split("=", 1)
            env[k] = v

    env.update(env_override)

    code = isolate_and_run(root, cmd, env, workdir)

    shutil.rmtree(root)
    if code != 0:
        sys.exit(code)