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

Check `Commands.txt` for comprehensive test cases that demonstrate:
- Cache hit/miss scenarios
- Container execution
- Environment variables
- Security/isolation verification
- Image management

Run tests with:

```bash
sudo python3 docksmith.py build -t myapp:latest sample_app
sudo python3 docksmith.py run myapp:latest
```
