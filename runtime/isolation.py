import os

def isolate_and_run(root, cmd, env, workdir):
    pid = os.fork()

    if pid == 0:
        os.chroot(root)
        os.chdir(workdir if workdir else "/")
        os.execvpe(cmd[0], cmd, env)
    else:
        os.wait()