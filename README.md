pylxc
=====

A simple python wrapper on LXC commands

> Note: This currently wraps lxc-* command line, probably will be converted to wrap liblxc instead using Cython or Swig

Usage
=====
You can query current containers using
    import lxc
    lxc.all_as_list()
    >> ['Container1', 'Container2', 'Container3']
    lxc.all_as_dict()
    >> {'Running': ['Container1']
        'Stopped': ['Container2', 'Container3']
       }

to get the running or stopped list
    import lxc
    lxc.running()
    >> ['Container1']
    lxc.stopped()
    >> ['Container2', 'Container3']

Check if a container exists
    import lxc
    lxc.exists("Container1")

You can also get notified when a certain container reaches a given state(s) asynchronously
    import lxc
    def myCallback():
        print "Hey, The Container is Running!"

    lxc.notify("Container2", "RUNNING", myCallback)
    lxc.notify("Container1", "RUNNING|STOPPED", myCallback)

You can also start the LXC Monitor to keep getting updates about certain container or a set of containers
    import lxc
    def myCallback(state):
        print "The state is now %s" % state

    lxc.monitor("Container1", myCallback)
    lxc.monitor("Container2", myCallback)

to stop monitoring a certain container
    import lxc
    lxc.unmonitor("Container1")

to stop the whole LXC Monitor
    import lxc
    lxc.stop_monitor()

