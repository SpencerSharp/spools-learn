import os
import sys
import signal

def send_signal(pid, sig):
    if pid > 0:
        try:
            os.kill(pid,sig)
        except:
            raise

def create_process():
    to_kill = os.fork()
    if to_kill == 0:
        signal.pause()
        sys.exit()
    if os.fork() == 0:
        if os.fork() != 0:
            sys.exit()
        send_signal(to_kill, signal.SIGUSR1)
        return True
    else:
        os.waitpid(to_kill, 0)
        return False