import os, shutil, json, tempfile, subprocess
from builder.parser import parse_docksmithfile
from builder.cache import compute_cache_key, check_cache, store_cache
from builder.cache import hash_directory
from builder.layers import create_layer
from utils.paths import init_dirs, IMAGES_DIR

def build(tag, context, no_cache=False):
    print("BUILD FUNCTION CALLED")

    init_dirs()

    instructions = parse_docksmithfile(os.path.join(context, "Docksmithfile"))

    workdir = ""
    env = {}
    layers = []
    prev_digest = "base"
    final_cmd = None

    temp_root = tempfile.mkdtemp()

    for i, (cmd, arg, line_no) in enumerate(instructions):
        print(f"Step {i+1}/{len(instructions)} : {cmd} {arg}")

        if cmd == "FROM":
            print("Using base image (mock)")
            continue

        elif cmd == "WORKDIR":
            workdir = arg

        elif cmd == "ENV":
            k, v = arg.split("=")
            env[k] = v

        elif cmd == "CMD":
            final_cmd = json.loads(arg)

        elif cmd in ["COPY", "RUN"]:
            
            if cmd == "COPY":
                dir_hash = hash_directory(context)
                key = compute_cache_key(prev_digest, cmd + arg + dir_hash, workdir, env)
            else:
                key = compute_cache_key(prev_digest, cmd + arg, workdir, env)

            cached = None if no_cache else check_cache(key)

            if cached:
                print("[CACHE HIT]")
                layers.append(cached)
                prev_digest = cached
                continue

            print("[CACHE MISS]")

            if cmd == "COPY":
                src, dest = arg.split()
                src_path = os.path.join(context, src)
                dest_path = os.path.join(temp_root, dest.lstrip("/"))

                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                    
                os.makedirs(dest_path, exist_ok=True)
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)

            elif cmd == "RUN":
                subprocess.run(arg, shell=True, cwd=temp_root)

            digest = create_layer(temp_root)
            store_cache(key, digest)

            layers.append(digest)
            prev_digest = digest

    manifest = {
        "name": tag.split(":")[0],
        "tag": tag.split(":")[1],
        "layers": layers,
        "config": {
            "Env": [f"{k}={v}" for k, v in env.items()],
            "Cmd": final_cmd,
            "WorkingDir": workdir
        }
    }

    path = os.path.join(IMAGES_DIR, tag.replace(":", "_") + ".json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("Build complete")