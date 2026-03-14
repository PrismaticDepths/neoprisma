
# Todo

[ ] timer for playback or autoclicker \
[ ] set how many loops \
[ ] editor/tas \
[ ] relative mouse \
[ ] move mouse only on clicks \
[ ] suppress hotkeys \
[ ] normalize hotkeysw

raceback (most recent call last):
File "/Users/jonahr/Documents/GitHub/neoprism/src/platform_macos.py", line 188, in __init__
conf_data=globalconfwizard.unpack(os.path.expanduser("~/.neoprisma"))
File "/Users/jonahr/Documents/GitHub/neoprism/src/globalconfwizard.py", line 117, in unpack
raise RuntimeError("NO_VERSION / Could not unpack configuration file: Possibly corrupted or invalid file, presumably an old version.")
RuntimeError: NO_VERSION / Could not unpack configuration file: Possibly corrupted or invalid file, presumably an old version.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
File "/Users/jonahr/Documents/GitHub/neoprism/src/platform_macos.py", line 636, in <module>
m = Main()
File "/Users/jonahr/Documents/GitHub/neoprism/src/platform_macos.py", line 196, in __init__
self.save_configurations()
~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/Users/jonahr/Documents/GitHub/neoprism/src/platform_macos.py", line 427, in save_configurations
globalconfwizard.pack(os.path.expanduser("~/.neoprisma"),self.conf_data)
~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/Users/jonahr/Documents/GitHub/neoprism/src/globalconfwizard.py", line 136, in pack
packed +=f"{value.name}&{key.upper()}&{value.pack()}\n"
~~~~~~~~~~^^
File "/Users/jonahr/Documents/GitHub/neoprism/src/globalconfwizard.py", line 41, in pack
return self._pack()
~~~~~~~~~~^^
File "/Users/jonahr/Documents/GitHub/neoprism/src/globalconfwizard.py", line 59, in _pack
assert type(self.real_value)==type(bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
