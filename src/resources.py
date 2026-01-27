import sys
import os

def resource_path(relative_path: str) -> str:
    """
    Return the absolute path to a resource, works both in dev and in PyInstaller bundle.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Development
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, relative_path)
