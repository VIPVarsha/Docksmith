import sys, os
from builder.executor import build
from runtime.container import run_container
from utils.paths import init_dirs, IMAGES_DIR

def images():
    for f in os.listdir(IMAGES_DIR):
        print(f.replace("_", ":").replace(".json", ""))

def rmi(tag):
    path = os.path.join(IMAGES_DIR, tag.replace(":", "_") + ".json")
    if os.path.exists(path):
        os.remove(path)
        print("Removed")
    else:
        print("Not found")

if __name__ == "__main__":
    init_dirs()

    # ✅ Handle no arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  build -t name:tag <context>")
        print("  run <name:tag>")
        print("  images")
        print("  rmi <name:tag>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "build":
        if len(sys.argv) < 5 or sys.argv[2] != "-t":
            print("Usage: build -t name:tag <context>")
            sys.exit(1)

        tag = sys.argv[3]
        context = sys.argv[4]
        build(tag, context)

    elif cmd == "run":
        if len(sys.argv) < 3:
            print("Usage: run <name:tag>")
            sys.exit(1)

        run_container(sys.argv[2])

    elif cmd == "images":
        images()

    elif cmd == "rmi":
        if len(sys.argv) < 3:
            print("Usage: rmi <name:tag>")
            sys.exit(1)

        rmi(sys.argv[2])

    else:
        print("Unknown command")