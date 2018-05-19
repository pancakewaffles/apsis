import asyncio
from   functools import partial
import getpass
import jinja2
import logging
from   ora import *
from   pathlib import Path
import shlex
import socket
import subprocess

from   . import lib
from   .types import *

log = logging.getLogger("program")

#-------------------------------------------------------------------------------

# FIXME: Elsewhere.

def expand(string, run):
    template = jinja2.Template(string)
    ns = {
        "run_id": run.run_id,
        "job_id": run.inst.job.job_id,
        **run.inst.args, 
    }
    return template.render(ns)


#-------------------------------------------------------------------------------

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%kZ"

class ProcessProgram:

    def __init__(self, argv):
        self.__argv = tuple( str(a) for a in argv )
        self.__executable = Path(argv[0])


    def __str__(self):
        return " ".join( shlex.quote(a) for a in self.__argv )


    def to_jso(self):
        return {
            "argv"      : list(self.__argv),
        }


    async def start(self, run):
        log.info("running: {}".format(run))

        # FIXME: Start / end time one level up.
        run.meta.update({
            "hostname"  : socket.gethostname(),
            "username"  : getpass.getuser(),
        })

        argv = [ expand(a, run) for a in self.__argv ]

        try:
            with open("/dev/null") as stdin:
                proc = await asyncio.create_subprocess_exec(
                    *argv, 
                    executable  =self.__executable,
                    stdin       =stdin,
                    # Merge stderr with stdin.  FIXME: Do better.
                    stdout      =asyncio.subprocess.PIPE,
                    stderr      =asyncio.subprocess.STDOUT,
                )
        except OSError as exc:
            raise ProgramError(str(exc))
        else:
            run.meta["pid"] = proc.pid
            return proc


    async def wait(self, run, proc):
        stdout, stderr  = await proc.communicate()
        return_code     = proc.returncode

        assert stderr is None
        assert return_code is not None

        run.meta["return_code"] = return_code
        run.output = stdout
        if return_code == 0:
            return
        else:
            raise ProgramFailure("return code = {}".format(return_code))



class ShellCommandProgram(ProcessProgram):

    def __init__(self, command):
        # FIXME: Which shell?
        command = str(command)
        super().__init__(["/bin/bash", "-c", command])
        self.__command = command


    def __str__(self):
        return self.__command



