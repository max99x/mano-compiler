from distutils.core import setup
import sys, platform
import py2exe

assert platform.system() == 'Windows', 'This setup is only for Windows.'

sys.argv.append('py2exe')
setup(options = {'py2exe': {'optimize': 2}},
      console = [{'script': 'compiler.py'}])
