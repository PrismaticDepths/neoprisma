import sys
import threading
from pynput._util import AbstractListener

def pynput_313(): 
    """Python 3.13 introduced a thread attribute that conflicts with pynput. This replaces the naming of said attribute within pynput, so it does not conflict with the new builtin attr."""
    if sys.version_info >= (3, 13):
        def get_pynput_handle(self):
            return getattr(self, '_pynput_handle', None)
        def set_pynput_handle(self, value):
            self._pynput_handle = value
        AbstractListener._handle = property(get_pynput_handle, set_pynput_handle) # Hopefully only run once