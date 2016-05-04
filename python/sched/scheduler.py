import errno
import logging
import os
import subprocess
import sys
import time

from   . import run
from   .instance import Instance

#-------------------------------------------------------------------------------

class Scheduler:

    def __init__(self, schedule_queue, instance_db):
        self.__schedule_queue = schedule_queue
        self.__instance_db = instance_db

        # Map from pid to subprocess.Popen for running processes.
        self.__procs = {}
        # Finished child pids.
        self.__done_pids = {}


    def clean_up(self):
        """
        Cleans up any terminated child processes for running instances.

        Performs nonblocking wait()'s for child processes, until no terminated
        children are left.  Collects their results and stores them in the
        instance DB.
        """
        # FIXME: Place instance processes into a separate process group, so
        # that we can wait for them without waiting for other random child
        # processes.

        while len(self.__procs) > 0:
            try:
                pid, status, usage = os.wait4(-1, os.WNOHANG)
            except ChildProcessError as exc:
                if exc.errno == errno.ECHILD:
                    # No (more) children.
                    log.error("wait4() returned ECHILD; no children!")
                    break
                else:
                    raise
            if pid == 0:
                # No zombie children.
                break

            logging.debug("child {} terminated".format(pid))
            try:
                proc = self.__procs.pop(pid)
            except KeyError:
                # Oops.  Not one of our child processes.
                logging.error("cleaned up non-instance child: {}".format(pid))
            else:
                instance = proc.instance
                self.__instance_db.set_result(instance, (status, usage))
                logging.debug("instance {} done".format(instance.id))


    def start(self):
        """
        Starts processes for instances in the ready queue.
        """
        while len(self.__schedule_queue) > 0:
            instance = self.__schedule_queue.pop()
            logging.debug("scheduler starting instance {}".format(instance.id))
            proc = run.start(instance.job)
            logging.debug(
                "child {} started for instance {}"
                .format(proc.pid, instance.id))

            proc.instance = instance
            self.__procs[proc.pid] = proc


    def run1(self):
        self.clean_up()
        self.start()


    def run_all(self, interval=0.1):
        while len(self.__schedule_queue) > 0 or len(self.__procs) > 0:
            self.run1()
            # FIXME: Hacky.
            time.sleep(interval)
        logging.debug("no ready or running jobs")



#-------------------------------------------------------------------------------

def schedule_instance(schedule_queue, instance):
    schedule_queue.append(instance)


