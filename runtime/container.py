import os, json, tempfile, shutil, sys, hashlib, tarfile, datetime
from utils.paths import IMAGES_DIR, LAYERS_DIR, FORENSICS_DIR
from utils.tar_utils import extract_tar
from runtime.isolation import isolate_and_run

def create_forensic_snapshot(root, tag):
    """Create a forensic snapshot of the container filesystem."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_tag = tag.replace(":", "_")
    snapshot_name = f"{safe_tag}_{timestamp}"
    
    # Create tarball of the filesystem
    tarball_path = os.path.join(FORENSICS_DIR, f"{snapshot_name}.tar.gz")
    with tarfile.open(tarball_path, "w:gz") as tar:
        tar.add(root, arcname=".")
    
    # Calculate SHA256 hash
    sha256_hash = hashlib.sha256()
    with open(tarball_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    hash_value = sha256_hash.hexdigest()
    hash_file = os.path.join(FORENSICS_DIR, f"{snapshot_name}.sha256")
    with open(hash_file, "w") as f:
        f.write(f"{hash_value}  {snapshot_name}.tar.gz\n")
    
    print(f"\n[FORENSIC] Snapshot created: {snapshot_name}")
    print(f"[FORENSIC] Location: {FORENSICS_DIR}/")
    print(f"[FORENSIC] SHA256: {hash_value}")

def run_container(tag, cmd_override=None, env_override={}, forensic_mode=False):
    path = os.path.join(IMAGES_DIR, tag.replace(":", "_") + ".json")

    if not os.path.exists(path):
        print("Image not found")
        sys.exit(1)

    with open(path) as f:
        manifest = json.load(f)

    root = tempfile.mkdtemp()

    for layer in manifest.get("layers", []):
        layer_path = os.path.join(LAYERS_DIR, layer + ".tar")
        if not os.path.exists(layer_path):
            print(f"Error: Backing layer {layer[:12]} is missing. Was it deleted by 'rmi'? Fix by rebuilding or running 'sudo python3 setup_base.py'.")
            shutil.rmtree(root)
            sys.exit(1)
        extract_tar(layer_path, root)

    cmd = cmd_override if cmd_override else manifest["config"].get("Cmd")
    if not cmd:
        print("Error: No CMD is defined in the image and no override command was provided.")
        shutil.rmtree(root)
        sys.exit(1)
    workdir = manifest["config"].get("WorkingDir", "/")

    env = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin"}
    
    for e in manifest["config"].get("Env", []):
        if "=" in e:
            k, v = e.split("=", 1)
            env[k] = v

    env.update(env_override)

    code = isolate_and_run(root, cmd, env, workdir)

    # Create forensic snapshot if enabled or if container failed
    if forensic_mode or code != 0:
        create_forensic_snapshot(root, tag)

    shutil.rmtree(root)
    if code != 0:
        sys.exit(code)