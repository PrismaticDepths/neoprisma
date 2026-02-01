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

def pack(fpath,data):
	
	with open(fpath,"w") as cfile:
		packed=""
		for key,value in data:
			packed += f"{key.upper()}% {value}\n"
		cfile.write(packed)