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
		
class CNVType:

	@classmethod
	def from_packed(cls,packed):
		return cls(cls._unpack(cls,packed))

	def __init__(self,name,real_value,description=""):

		self.name = name
		self.real_value = real_value
		self.description = description

	def pack(self):
		return self._pack()
	
	def set_value_from_packed(self,packed):
		self.real_value = self._unpack(packed)
	def set_value(self,val):
		print(val)
		self.real_value = val
	
	def get_value(self):
		if hasattr(self,"_get_value"):
			return self._get_value()
		else:
			return self.real_value


class CNVBoolean(CNVType):

	def __init__(self,value,description=""):
		super().__init__("bool",value,description)

	def _pack(self):
		assert type(self.real_value)==type(True)
		return "yes" if self.real_value==True else "no"
	def _unpack(self,value:str):
		if str(value).strip().lower() == "yes":
			return True
		elif str(value).strip().lower() == "no":
			return False
		else: raise TypeError("cannot unpack non yes/no value")
	
class CNVString(CNVType):

	def __init__(self,value,**kwargs):
		super().__init__("string",value,**kwargs)

	def _pack(self):
		return str(self.real_value)
	def _unpack(self,value):
		return str(value).strip()
	
class CNVInteger(CNVType):

	def __init__(self,value,smin=None,smax=None,description=""):
		super().__init__("int",value,description)

	def _pack(self):
		return str(self.real_value)
	def _unpack(self,value):
		return int(str(value).strip())
	
class CNVKeyset(CNVType):

	def __init__(self,value,**kwargs):
		super().__init__("keyset",value,**kwargs)

	def _pack(self):
		return " ".join([str(v) for v in self.real_value])
	
	def _unpack(self,value):
		return set(int(v) for v in value.split(" "))

NAME_TO_TYPE = {
	"bool":CNVBoolean,
	"string":CNVString,
	"keyset":CNVKeyset,
	"int":CNVInteger,
}

FMT = [
	"type",
	"name",
	"value"
]

SEP = "&"

def unpack(fpath):
		
	with open(fpath,"r") as cfile:
		data = {}
			
		for line in cfile.readlines():
			tmp = line.split(SEP,len(FMT)-1)
			typ = tmp[0].strip().lower()
			try:
				key = tmp[1].strip().upper()
			except IndexError:
				raise RuntimeError("NO_VERSION / Could not unpack configuration file: Possibly corrupted or invalid file, presumably an old version.")
			val=tmp[2]
			data[key] = NAME_TO_TYPE[typ].from_packed(val)
			

	if not "DOC" in data: raise Exception("Could not unpack configuration file: Missing DOC tag.")
	else:
		if data["DOC"].get_value() != "NEOPRISMA CONFIGURATION DATA": raise Exception("Non-compatible DOC tag.")
	if not "VERSION" in data: raise RuntimeError("NO_VERSION / Could not unpack configuration file: Missing VERSION tag.")
	else:
		if data["VERSION"].get_value() < 2: raise RuntimeError("LOW_VERSION / Config version too low")
	return data

def pack(fpath,data:dict[str,CNVType]):

	with open(fpath,"w") as cfile:
		packed=""
		for key,value in data.items():
			packed +=f"{value.name}&{key.upper()}&{value.pack()}\n"
		cfile.write(packed)