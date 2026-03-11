""" 
Neoprisma Copyright (C) 2026 PrismaticDepths <prismaticdepths@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

import os, sys

if getattr(sys, "frozen", False):
	BASE = sys._MEIPASS
else:
	BASE = os.path.dirname(__file__)

SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
	sys.path.insert(0, SRC)
		
def unpack(fpath):
		
	with open(fpath,"r") as cfile:
		data = {}
			
		for line in cfile.readlines():
			key=line.split("%")[0].strip().upper()
			val=line.split("%")[1].strip()
			data[key] = val
	
	if not "DOC" in data: raise RuntimeError("Could not unpack configuration file: Missing DOC tag.")
	else:
		if data["DOC"] != "NEOPRISMA CONFIGURATION DATA": raise RuntimeError("Non-compatible DOC tag.")
	return data

def pack(fpath,data:dict):

	with open(fpath,"w") as cfile:
		packed=""
		for key,value in data.items():
			packed += f"{key.upper()}% {value}\n"
		cfile.write(packed)
