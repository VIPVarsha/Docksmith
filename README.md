# Docksmith - A Docker-like Container System

A mini Docker-like container system built in Python with support for layered builds, caching, and runtime isolation using chroot.

## Project Description

Docksmith is a lightweight container system implementation that mimics Docker's core functionality. It enables users to:

- **Layered Builds**: Create container images using a layered architecture similar to Docker
- **Caching Mechanism**: Intelligently cache build layers to speed up subsequent builds
- **Runtime Isolation**: Execute containers in isolated environments using chroot for filesystem isolation
- **Image Management**: Store, list, and manage container images with metadata
- **Dockerfile-like Syntax**: Use `Docksmithfile` to define container images with familiar commands (FROM, RUN, COPY, WORKDIR, ENV, CMD)

The system consists of:
- **Builder Module**: Parses Docksmithfiles, executes build instructions, manages layers
- **Runtime Module**: Handles container execution and filesystem isolation
- **Caching Module**: Implements layer caching using hash-based validation
- **Utils Module**: Provides helper functions for path management and file operations

## Prerequisites

Before running Docksmith, ensure you have:

- **Python 3.x**: The project is written in Python 3
- **Linux/Unix System**: Docksmith requires Linux (chroot functionality)
- **sudo Privileges**: Container operations require root/sudo access due to filesystem isolation requirements
- **Alpine Linux minirootfs**: Automatically downloaded during setup

## How to Run

### 1. Initial Setup

First, initialize the base image by downloading the Alpine Linux minirootfs:

```bash
sudo python3 setup_base.py
```

This command downloads the Alpine Linux minimal root filesystem and sets up the base layer for all containers.

### 2. Build a Container Image

To build a container image from a Docksmithfile:

```bash
sudo python3 docksmith.py build -t myapp:latest sample_app
```

This builds an image tagged as `myapp:latest` from the `sample_app` directory. The build process:
- Parses the `Docksmithfile`
- Executes build instructions (RUN, COPY, etc.)
- Creates layers and caches them for future builds
- Stores the image metadata

### 3. Run a Container

To execute a built container image:

```bash
sudo python3 docksmith.py run myapp:latest
```

This runs the container with the specified tag in an isolated environment.

#### Forensic Mode (Security Audits)

For security investigations and post-incident analysis, use the `--forensic` flag:

```bash
sudo python3 docksmith.py run --forensic myapp:latest
```

**What Forensic Mode Does:**
- Automatically captures the container's filesystem state when it exits
- Creates an immutable, read-only snapshot of the final state
- Generates a deterministic tarball archive (stored in `.docksmith/forensics/`)
- Computes a cryptographic SHA256 hash for integrity verification
- Particularly useful for analyzing failed containers or security breaches

**Forensic Output:**
When forensic mode is enabled, a snapshot is saved with the format:
```
.docksmith/forensics/
├── myapp_latest_TIMESTAMP_HASH.tar.gz     # Compressed filesystem snapshot
└── myapp_latest_TIMESTAMP_HASH.sha256     # Integrity hash file
```

**Example Usage:**
```bash
# Run container with forensic capture enabled
sudo python3 docksmith.py run --forensic myapp:latest

# Container exits or encounters error
# Automatic snapshot saved to .docksmith/forensics/

# Verify snapshot integrity
sha256sum -c myapp_latest_TIMESTAMP_HASH.sha256

# Extract and examine filesystem
tar -xzf myapp_latest_TIMESTAMP_HASH.tar.gz
```

This enables workflows like:
- **Malware Analysis**: Preserve container state for security investigation
- **Compliance Audits**: Generate immutable audit trails for forensic reports
- **Debugging**: Inspect exact filesystem state when unexpected errors occur

### 4. List Images

To view all built container images:

```bash
sudo python3 docksmith.py images
```

This displays a table showing image name, tag, layer ID, and creation time.

### 5. Remove Images

To delete a container image and its associated layers:

```bash
sudo python3 docksmith.py rmi myapp:latest
```

This removes the image with the specified tag and all its cached layers from the system.

### 6. Docksmithfile Format

Create a `Docksmithfile` in your application directory with commands similar to Dockerfile:

```dockerfile
FROM alpine:3.18
WORKDIR /app
COPY . /app
ENV NAME=World
RUN echo "Build Done"
CMD ["/bin/sh", "app.sh"]
```

Supported commands:
- `FROM`: Base image to build upon
- `WORKDIR`: Set working directory inside container
- `COPY`: Copy files from host to container
- `ENV`: Set environment variables
- `RUN`: Execute commands during build
- `CMD`: Default command to run when container starts

### 7. Testing & Demonstrations

#### Test 1: Build + Cache HIT

Test the caching mechanism by building the same image twice:

```bash
sudo python3 docksmith.py build -t myapp:latest sample_app
```

Run the command twice:
- **First run**: Should show `[CACHE MISS]` for all layer-producing steps
- **Second run**: Should show `[CACHE HIT]` for all steps (instant build)

This demonstrates that Docksmith correctly caches layers and reuses them when nothing has changed.

#### Test 2: Cache MISS (after file change)

Modify a source file and rebuild to trigger cache invalidation:

```bash
# Edit sample_app/app.sh - change the echo message
echo "#!/bin/sh" > sample_app/app.sh
echo 'echo "Hello Changed"' >> sample_app/app.sh

# Rebuild
sudo python3 docksmith.py build -t myapp:latest sample_app
```

Expected output:
- The `COPY` step and all subsequent steps show `[CACHE MISS]`
- Earlier steps (FROM) still show `[CACHE HIT]`

This demonstrates cache invalidation: when source files change, only affected layers are rebuilt.

#### Test 3: Run Container

Execute the built container to verify it produces output:

```bash
sudo python3 docksmith.py run myapp:latest
```

Expected output:
- Container starts and executes the CMD
- Outputs: `Hello Changed`
- Container exits cleanly

#### Test 4: Environment Variables

Test ENV variable usage and override:

```bash
# Edit sample_app/Docksmithfile
# Change: ENV NAME=Universe

# Edit sample_app/app.sh
# Change the echo to: echo "Hello $NAME"

# Build
sudo python3 docksmith.py build -t myapp:latest sample_app

# Run with default ENV
sudo python3 docksmith.py run myapp:latest
# Output: Hello Universe

# Run with ENV override
sudo python3 docksmith.py run -e NAME=Docksmith myapp:latest
# Output: Hello Docksmith
```

This demonstrates:
- ENV variables defined in Docksmithfile are injected into containers
- -e flag allows runtime overrides

#### Test 5: Isolation (Security Test)

Verify that files written inside a container cannot escape to the host:

```bash
# Edit sample_app/app.sh to attempt a filesystem escape
# cat > sample_app/app.sh << 'EOF'
#!/bin/sh
echo "HACK" > /outside.txt
echo "Isolation test"
echo "Checking if /outside.txt was created..."
ls /
# EOF

# Build
sudo python3 docksmith.py build -t myapp:latest sample_app

# Run
sudo python3 docksmith.py run myapp:latest

# Check host filesystem
ls /outside.txt 2>&1
```

Expected result:
- Container output shows `/outside.txt` was created inside container
- **PASS/FAIL**: `/outside.txt` does NOT exist on host filesystem
- This verifies container isolation is working (chroot prevents escape)

#### Test 6: List Images

View all built images with metadata:

```bash
sudo python3 docksmith.py images
```

Expected output:
```
NAME                 TAG        ID              CREATED
myapp                latest     <12-char hash>  2026-04-15 14:30:22
```

Columns displayed:
- **NAME**: Image name
- **TAG**: Image tag
- **ID**: First 12 characters of layer digest
- **CREATED**: Creation timestamp

#### Test 7: Internal Storage

Verify the directory structure created by Docksmith:

```bash
ls -la ~/.docksmith/
```

Expected output:
```
drwxr-xr-x  4 root root 4096 Apr 15 14:30 .docksmith
├── images/        # JSON manifests (one per image)
├── layers/        # Content-addressed tar files (named by SHA256 digest)
├── cache/         # Cache index (maps cache keys to layer digests)
└── forensics/     # Forensic snapshots (if --forensic flag was used)
```

Key points:
- `images/`: One JSON file per image named `<name_tag>.json`
- `layers/`: Tar files named by SHA256 digest of their content
- `cache/`: Readonly files mapping build cache keys to layer digests
- `forensics/`: Forensic snapshots with .tar.gz and .sha256 files

#### Full Demo Workflow

Complete sequence demonstrating all features:

```bash
# 1. Initial setup (once)
sudo python3 setup_base.py

# 2. Cold build (all CACHE MISS)
sudo python3 docksmith.py build -t myapp:latest sample_app

# 3. Warm build (all CACHE HIT)
sudo python3 docksmith.py build -t myapp:latest sample_app

# 4. Run container
sudo python3 docksmith.py run myapp:latest

# 5. List images
sudo python3 docksmith.py images

# 6. Run with ENV override
sudo python3 docksmith.py run -e NAME=CustomValue myapp:latest

# 7. Run with forensic mode (security audit)
sudo python3 docksmith.py run --forensic myapp:latest

# 8. Check internal storage
ls -la ~/.docksmith/layers/
ls -la ~/.docksmith/images/

# 9. Remove image
sudo python3 docksmith.py rmi myapp:latest
```

This comprehensive workflow demonstrates:
- ✅ Build caching (MISS/HIT)
- ✅ Container execution
- ✅ Environment variable injection and override
- ✅ Process isolation
- ✅ Image management
- ✅ Forensic capabilities
- ✅ Content-addressed layer storage
