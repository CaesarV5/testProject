# from py2exe.build_exe import py2exe
from distutils.core import setup
import py2exe

# setup(windows=[{"script":"guiQt.py"}], options={"py2exe":{"includes":["sip"]}})
setup(windows=[{"script": "guiQt.py"}], options={"py2exe": {"dll_excludes": ["MSVCP90.dll"], "includes": ["sip"]}})
