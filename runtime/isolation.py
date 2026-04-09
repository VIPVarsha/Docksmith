import os

def isolate_and_run(root, cmd, env, workdir):
    # No chroot (for portability)
    os.chdir(root)

    
    if workdir:
        target_dir = os.path.join(root, workdir.lstrip("/"))
        if os.path.exists(target_dir):
            os.chdir(target_dir)

    
    if cmd and len(cmd) > 1:
        script = cmd[1]
        if not os.path.exists(script):
            alt = os.path.join(root, script)
            if os.path.exists(alt):
                cmd[1] = alt

    os.execvpe(cmd[0], cmd, env)