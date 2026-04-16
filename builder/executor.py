import os, shutil, json, tempfile, sys, time
from builder.parser import parse_docksmithfile
from builder.cache import compute_cache_key, check_cache, store_cache, hash_directory
from builder.layers import create_layer
from utils.paths import init_dirs, IMAGES_DIR, LAYERS_DIR
from utils.tar_utils import extract_tar
from utils.hashing import sha256_bytes
from runtime.isolation import isolate_and_run

def build(tag, context, no_cache=False):
    print("BUILD FUNCTION CALLED")
    init_dirs()
    instructions = parse_docksmithfile(os.path.join(context, "Docksmithfile"))

    workdir = ""
    env = {}
    layers = []
    prev_digest = "base"
    final_cmd = None

    for i, (cmd, arg, line_no) in enumerate(instructions):
        print(f"Step {i+1}/{len(instructions)} : {cmd} {arg}")

        if cmd == "FROM":
            base_tag = arg
            base_manifest_path = os.path.join(IMAGES_DIR, base_tag.replace(":", "_") + ".json")
            if os.path.exists(base_manifest_path):
                with open(base_manifest_path) as f:
                    bm = json.load(f)
                    layers.extend(bm.get("layers", []))
                    if layers:
                        prev_digest = layers[-1]
                    for e in bm.get("config", {}).get("Env", []):
                        if "=" in e:
                            k, v = e.split("=", 1)
                            env[k] = v
                    workdir = bm.get("config", {}).get("WorkingDir", "")
                    final_cmd = bm.get("config", {}).get("Cmd", None)
            else:
                print(f"Base image {base_tag} not found. Please setup base image first.")
                sys.exit(1)
            continue

        elif cmd == "WORKDIR":
            workdir = arg
        elif cmd == "ENV":
            k, v = arg.split("=", 1)
            env[k] = v
        elif cmd == "CMD":
            final_cmd = json.loads(arg)
        elif cmd in ["COPY", "RUN"]:
            if cmd == "COPY":
                dir_hash = hash_directory(context)
                key = compute_cache_key(prev_digest, cmd + " " + arg + dir_hash, workdir, env)
            else:
                key = compute_cache_key(prev_digest, cmd + " " + arg, workdir, env)

            cached = None if no_cache else check_cache(key)

            if cached:
                print("[CACHE HIT]")
                layers.append(cached)
                prev_digest = cached
                continue

            print("[CACHE MISS]")
            
            temp_root = tempfile.mkdtemp()
            for layer in layers:
                layer_path = os.path.join(LAYERS_DIR, layer + ".tar")
                if not os.path.exists(layer_path):
                    print(f"Error: Backing layer {layer[:12]} is missing. Was it deleted by 'rmi'? Fix by running 'sudo python3 setup_base.py'.")
                    shutil.rmtree(temp_root)
                    sys.exit(1)
                extract_tar(layer_path, temp_root)

            if cmd == "COPY":
                src, dest = arg.split(" ", 1)
                src_path = os.path.join(context, src)
                dest_path = os.path.join(temp_root, dest.lstrip("/"))
                if os.path.exists(dest_path):
                    if os.path.isdir(dest_path):
                        shutil.rmtree(dest_path)
                    else:
                        os.remove(dest_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dest_path)

            elif cmd == "RUN":
                run_env = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"}
                run_env.update(env)
                code = isolate_and_run(temp_root, ["/bin/sh", "-c", arg], run_env, workdir)
                if code != 0:
                    print(f"RUN failed with exit code {code}")
                    sys.exit(code)

            digest = create_layer(temp_root)
            store_cache(key, digest)
            layers.append(digest)
            prev_digest = digest
            shutil.rmtree(temp_root)

    t_created = int(time.time())
    path = os.path.join(IMAGES_DIR, tag.replace(":", "_") + ".json")
    if os.path.exists(path):
        with open(path) as f:
            old_manifest = json.load(f)
            if old_manifest.get("layers", []) == layers:
                t_created = old_manifest.get("created", t_created)

    manifest = {
        "name": tag.split(":")[0],
        "tag": tag.split(":")[1] if ":" in tag else "latest",
        "digest": "",
        "created": t_created,
        "config": {
            "Env": [f"{k}={v}" for k, v in env.items()],
            "Cmd": final_cmd,
            "WorkingDir": workdir
        },
        "layers": layers
    }

    # Compute manifest digest: serialize with digest="", hash it, then set it
    manifest_json = json.dumps(manifest, separators=(',', ':'), sort_keys=True)
    manifest_hash = sha256_bytes(manifest_json.encode())
    manifest["digest"] = f"sha256:{manifest_hash}"

    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("Build complete")