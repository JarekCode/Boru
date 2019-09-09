# https://stackoverflow.com/questions/1057431/how-to-load-all-modules-in-a-folder
# https://stackoverflow.com/questions/44834/can-someone-explain-all-in-python
# The code below gathers all the files in the folder and stores them in a variable __all__
# This variable is read whenever somewhere in the scheduler in /opt/boru code is written: ' from awsPlugins import * 
# the '*' in the code reads the __all__ variable'
from os.path import dirname, basename, isfile, join
import glob
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
