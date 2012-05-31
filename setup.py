from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

version = '0.0.1'

setup(name='pylxc',
      description="A python wrapper for Linux Containers (LXC)",
      long_description="A python wrapper for LXC commands",
      version=version,
      url='https://github.com/cloud9ers/pylxc',
      author="Cloud Niners Ltd.",
      author_email="asoliman@cloud9ers.com",
      packages=['lxc'],
      zip_safe=True,
      license = "LGPLv3",
      classifiers = ['Development Status :: 5 - Production/Stable',
                     'Intended Audience :: Developers',
                     'Intended Audience :: System Administrators',
                     'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
                     'Operating System :: POSIX :: Linux',
                     'Programming Language :: Python :: 2.7',
                     'Topic :: System :: Systems Administration'],
      
      )
