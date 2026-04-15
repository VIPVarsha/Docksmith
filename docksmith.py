import sys, os, json, datetime
from builder.executor import build
from runtime.container import run_container
from utils.paths import init_dirs, IMAGES_DIR, LAYERS_DIR

def images():
    print(f"{'NAME':<20} {'TAG':<10} {'ID':<15} {'CREATED':<20}")
    for f in os.listdir(IMAGES_DIR):
        if not f.endswith(".json"): continue
        path = os.path.join(IMAGES_DIR, f)
        with open(path) as file:
            try:
                manifest = json.load(file)
            except:
                continue
        
        name = manifest.get("name", "<none>")
        tag = manifest.get("tag", "latest")
        layers = manifest.get("layers", [])
        layer_id = layers[-1][:12] if layers else "<none>"
        
        created = manifest.get("created", 0)
        if created > 0:
            created_str = datetime.datetime.fromtimestamp(created).strftime('%Y-%m-%d %H:%M:%S')
        else:
            created_str = "Unknown"
        
        print(f"{name:<20} {tag:<10} {layer_id:<15} {created_str:<20}")

def rmi(tag):
    path = os.path.join(IMAGES_DIR, tag.replace(":", "_") + ".json")
    if os.path.exists(path):
        with open(path) as f:
            manifest = json.load(f)
        for layer in manifest.get("layers", []):
            layer_path = os.path.join(LAYERS_DIR, layer + ".tar")
            if os.path.exists(layer_path):
                os.remove(layer_path)
        os.remove(path)
        print(f"Removed image {tag} and its layers")
    else:
        print("Not found")

if __name__ == "__main__":
    init_dirs()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  build -t name:tag [--no-cache] <context>")
        print("  run [--forensic] <name:tag> [cmd...] [-e KEY=VALUE ...]")
        print("  images")
        print("  rmi <name:tag>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "build":
        if "-t" not in sys.argv:
            print("Usage: build -t name:tag [--no-cache] <context>")
            sys.exit(1)
        tag_idx = sys.argv.index("-t") + 1
        tag = sys.argv[tag_idx]
        no_cache = "--no-cache" in sys.argv
        context_args = [a for a in sys.argv[2:] if a != "-t" and a != tag and a != "--no-cache"]
        if not context_args:
            print("Missing context")
            sys.exit(1)
        context = context_args[0]
        build(tag, context, no_cache)

    elif cmd == "run":
        if len(sys.argv) < 3:
            print("Usage: run [--forensic] <name:tag> [cmd...] [-e KEY=VALUE ...]")
            sys.exit(1)

        forensic_mode = False
        tag_idx = 2
        
        if sys.argv[2] == "--forensic":
            forensic_mode = True
            tag_idx = 3
            if len(sys.argv) < 4:
                print("Usage: run [--forensic] <name:tag> [cmd...] [-e KEY=VALUE ...]")
                sys.exit(1)
        
        tag = sys.argv[tag_idx]
        env_override = {}
        cmd_override = []
        
        i = tag_idx + 1
        while i < len(sys.argv):
            if sys.argv[i] == "-e":
                if i + 1 < len(sys.argv):
                    if "=" in sys.argv[i+1]:
                        k, v = sys.argv[i+1].split("=", 1)
                        env_override[k] = v
                    i += 2
                else:
                    break
            else:
                cmd_override.append(sys.argv[i])
                i += 1
                
        if not cmd_override:
            cmd_override = None

        run_container(tag, cmd_override, env_override, forensic_mode)

    elif cmd == "images":
        images()

    elif cmd == "rmi":
        if len(sys.argv) < 3:
            print("Usage: rmi <name:tag>")
            sys.exit(1)
        rmi(sys.argv[2])

    else:
        print("Unknown command")