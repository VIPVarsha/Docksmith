import os

def isolate_and_run(root, cmd, env, workdir):
    pid = os.fork()

    if pid == 0:
        os.chroot(root)
        os.chdir(workdir if workdir else "/")
        os.execvpe(cmd[0], cmd, env)
    else:
        pid, status = os.waitpid(pid, 0)
        code = os.waitstatus_to_exitcode(status) if hasattr(os, "waitstatus_to_exitcode") else os.WEXITSTATUS(status)
        return code