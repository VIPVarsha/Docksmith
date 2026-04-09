import os, json, tempfile, shutil
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

    # Extract layers
    for layer in manifest["layers"]:
        extract_tar(os.path.join(LAYERS_DIR, layer + ".tar"), root)

    cmd = cmd_override if cmd_override else manifest["config"]["Cmd"]
    workdir = manifest["config"]["WorkingDir"]

    # Environment
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin"

    for e in manifest["config"]["Env"]:
        k, v = e.split("=")
        env[k] = v

    env.update(env_override)

    
    if cmd and cmd[0] == "python3":
        cmd[0] = "python3"

    isolate_and_run(root, cmd, env, workdir)

    shutil.rmtree(root)