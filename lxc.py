import subprocess
import logging
import threading, select
import pty
import os
import signal


class ContainerAlreadyExists(Exception): pass
class ContainerAlreadyRunning(Exception): pass
class ContainerNotExists(Exception): pass


_logger = logging.getLogger("pylxc")
_monitor = None  


class _LXCMonitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._process = None
        self._monitors = {}
        
    def run(self):
        master, slave = pty.openpty()
        cmd = ['lxc-monitor', '-n', '.*']
        self._process = subprocess.Popen(cmd, stdout=slave, bufsize=1)
        stdout = os.fdopen(master)
        while self._process.poll() is None:
            ready, _, _ = select.select([stdout], [], [], 0.1)
            if ready:
                logging.debug("Waiting for state change")
                state = stdout.readline()
                inf = state.strip().split()
                container = inf[0].strip("'")
                state = inf[-1].strip('[]')
                if container in self._monitors:
                    logging.debug("State of container '%s' changed to '%s'", container, state)
                    self._monitors[container](state)
        _logger.info("LXC Monitor stopped!")
    
    def add_monitor(self, name, callback):
        self._monitors[name] = callback
    
    def rm_monitor(self, name):
        self._monitors.pop(name)
    
    def is_monitored(self, name):
        return name in self._monitors
    
    def kill(self):
        try:
            self._process.terminate()
            self._process.wait()
        except:
            pass
        self.join() 

        
def create(name, config_file=None, template=None, backing_store=None, template_options=None):
    '''
    Create a new container
    raises ContainerAlreadyExists exception if the container name is reserved already.
    
    :param template_options: Options passed to the specified template
    :type template_options: list or None
    
    '''
    if exists(name):
        raise ContainerAlreadyExists("The Container %s is already created!" % name)
    cmd = ['lxc-create', '-n', name]

    if config_file:
        cmd += ['-f', config_file]
    if template:
        cmd += ['-t', template]
    if backing_store:
        cmd += ['-B', backing_store]
    if template_options:
        cmd += ['--'] + template_options
            
    if subprocess.check_call(cmd) == 0:
        if not exists(name):
            _logger.critical("The Container %s doesn't seem to be created! (options: %s)", name, cmd[3:])
            raise ContainerNotExists("The container (%s) does not exist!" % name)

        _logger.info("Container %s has been created with options %s", name, cmd[3:])


def exists(name):
    '''
    checks if a given container is defined or not
    '''
    if name in all_as_list():
        return True
    return False


def running():
    ''' 
    returns a list of the currently running containers
    '''
    return all_as_dict()['Running']


def stopped():
    '''
    returns a list of the stopped containers
    '''
    return all_as_dict()['Stopped']


def all_as_dict():
    '''
    returns a dict {'Running': ['cont1', 'cont2'], 
                    'Stopped': ['cont3', 'cont4']
                    }
                    
    '''
    cmd = ['lxc-list']
    out = subprocess.check_output(cmd).splitlines()
    stopped = []
    running = []
    current = None
    for c in out:
        c = c.strip()
        if c == 'RUNNING':
            current = running
            continue
        if c == 'STOPPED':
            current = stopped
            continue
        if not len(c):
            continue
        current.append(c)
    return {'Running': running,
            'Stopped': stopped}
         

def all_as_list():
    '''
    returns a list of all defined containers
    '''
    as_dict = all_as_dict()
    return as_dict['Running'] + as_dict['Stopped'] 


def start(name, config_file=None):
    '''
    starts a container in daemon mode
    '''
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    if name in running():
        raise ContainerAlreadyRunning('The container %s is already started!' % name)
    cmd = ['lxc-start', '-n', name, '-d']
    if config_file:
        cmd += ['-f', config_file]
    subprocess.check_call(cmd)


def kill(name, signal):
    '''
    sends a kill signal to process 1 of ths container <name>
    :param signal: numeric signal
    '''
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    cmd = ['lxc-kill', '--name=%s' % name, signal]
    subprocess.check_call(cmd)


def shutdown(name, wait=False, reboot=False):
    '''
    graceful shutdown sent to the container
    :param wait: should we wait for the shutdown to complete?
    :param reboot: reboot a container, ignores wait
    '''
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    cmd = ['lxc-shutdown', '-n', name]
    if wait:
        cmd += ['-w']
    if reboot:
        cmd += ['-r']
        
    subprocess.check_call(cmd)    


def destroy(name):
    '''
    removes a container [stops a container if it's running and]
    raises ContainerNotExists exception if the specified name is not created
    '''
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    cmd = ['lxc-destory', '-f', '-n', name]
    subprocess.check_call(cmd)


def monitor(name, callback):
    '''
    monitors actions on the specified container,
    callback is a function to be called on 
    '''
    global _monitor 
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    if _monitor:
        if _monitor.is_monitored(name):
            raise Exception("You are already monitoring this container (%s)" % name)
    else:
        _monitor = _LXCMonitor()
        logging.info("Starting LXC Monitor")
        _monitor.start()
        def kill_handler(sg, fr):
            stop_monitor()
        signal.signal(signal.SIGTERM, kill_handler)
        signal.signal(signal.SIGINT, kill_handler)
    _monitor.add_monitor(name, callback)
            

def unmonitor(name):
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    if not _monitor:
        raise Exception("LXC Monitor is not started!")
    if not _monitor.is_monitored(name):
        raise Exception("This container (%s) is not monitored!" % name)
    _monitor.rm_monitor(name)


def stop_monitor():
    global _monitor
    if _monitor:
        logging.info("Killing LXC Monitor")
        _monitor.kill()
        _monitor = None
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        
def freeze(name):
    '''
    freezes the container
    '''
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    cmd = ['lxc-freeze', '-n', name]
    subprocess.check_call(cmd)


def unfreeze(name):
    '''
    unfreezes the container
    '''
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    cmd = ['lxc-unfreeze', '-n', name]
    subprocess.check_call(cmd)


def info(name):
    '''
    returns info dict about the specified container
    '''
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)
    cmd = ['lxc-info', '-n', name]
    out = subprocess.check_output(cmd).splitlines()
    info = {}
    for line in out:
        k, v = line.split()
        info[k] = v
    return info


def checkconfig():
    '''
    returns the output of lxc-checkconfig
    '''
    cmd = ['lxc-checkconfig']
    return subprocess.check_output(cmd)


def notify(name, states, callback):
    '''
    executes the callback function with no parameters when the container reaches the specified state or states
    states can be or-ed or and-ed
        notify('test', 'STOPPED', letmeknow)
        
        notify('test', 'STOPPED|RUNNING', letmeknow)
    '''
    if not exists(name):
        raise ContainerNotExists("The container (%s) does not exist!" % name)

    cmd = ['lxc-wait', '-n', name, '-s', states]
    def th():
        subprocess.check_call(cmd)
        callback()
    _logger.info("Waiting on states %s for container %s", states, name)
    threading.Thread(target=th).start()