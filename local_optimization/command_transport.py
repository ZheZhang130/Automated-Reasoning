"""Deliver long, unchanged model commands without Windows/Linux argv-length limits."""
import hashlib
import os
import shlex
import subprocess
import time
import uuid


def execute_stdin_script(env,action,cwd,timeout,delegate):
    command=action['command'];payload=command.encode('utf-8')
    if b'\x00' in payload:raise ValueError('NUL is not a valid shell argument')
    path='/tmp/csc2108-command-'+uuid.uuid4().hex+'.sh'
    cwd=cwd or env.config.cwd
    cmd=[env.config.executable,'exec','-i','-w',cwd]
    for key in env.config.forward_env:
        if (value:=os.getenv(key)) is not None:cmd+=['-e',key+'='+value]
    for key,value in env.config.env.items():cmd+=['-e',key+'='+value]
    writer="import sys\nwith open(sys.argv[1], 'xb') as target:\n target.write(sys.stdin.buffer.read())\n"
    cmd += [env.container_id,'python','-I','-c',writer,path]
    before=len(env.evidence)
    try:
        # Binary stdin preserves UTF-8 and LF exactly on Windows. The original
        # budget/timeout/output/candidate logic still executes the short loader.
        upload=subprocess.run(cmd,input=payload,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              timeout=max(.1,min(10,env.deadline-time.monotonic())))
        if upload.returncode:
            raise RuntimeError('Docker command upload failed: '+upload.stderr.decode('utf-8',errors='replace')[-2000:])
        # Bash read preserves all trailing newlines; eval runs only INSIDE the
        # existing isolated container. Docker stdin for the actual action stays
        # closed, so candidate stdin cannot consume the transport script.
        loader='IFS= read -r -d "" _CSC2108_COMMAND < '+shlex.quote(path)+'; eval -- "$_CSC2108_COMMAND"'
        return delegate(action|{'command':loader},cwd,timeout=timeout)
    finally:
        for event in env.evidence[before:]:
            event.update(command=command,transport='binary_stdin_script',command_bytes=len(payload),
                         command_sha256=hashlib.sha256(payload).hexdigest())
        if env.container_id:
            try:
                subprocess.run([env.config.executable,'exec',env.container_id,'rm','-f',path],
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
            except (OSError,subprocess.TimeoutExpired):
                pass  # Container cleanup also removes this private tmpfs file.
