#!/usr/bin/env python

import os.path
import ConfigParser

class Settings():
	def __init__(self):
		#Set defaults
		self.scanMode_LE=False
		self.scanMode_Disc=False
		self.scanMode_NonDisc=False
		
		self.readTimeout_Disc=0
		self.readTimeout_NonDisc=0
		
		self.baseServer_URL=None
		self.baseServer_Timeout=8
		self.baseServer_Recache=60
		self.baseServer_Reader="Unknown"
		
		self.logging_File="vestigo.log"
		self.logging_MaxSize=1024*1024 # 1MB
		self.logging_FileCount=5
		self.logging_UseLog=False
		self.logging_STDOUT=True
		
		
		if not os.path.isfile("vestigo.ini"):
			raise "Error reading configuration file"
		
		Config = ConfigParser.ConfigParser()
		Config.read("vestigo.ini")
	
		try: self.scanMode_LE=Config.getboolean("Scan Modes","le") 
		except: pass
		try: self.scanMode_Disc=Config.getboolean("Scan Modes","discoverable") 
		except: pass
		try: self.scanMode_NonDisc=Config.getboolean("Scan Modes","nondiscoverable") 
		except: pass
	
		try: self.readTimeout_Disc=Config.get("Read Timeout","discoverable") 
		except: pass
		try: self.readTimeout_NonDisc=Config.get("Read Timeout","nondiscoverable") 
		except: pass
	
		try: self.baseServer_URL=Config.get("Base Server","url") 
		except: pass
		try: self.baseServer_Timeout=Config.get("Base Server","timeout") 
		except: pass
		try: self.baseServer_Recache=Config.get("Base Server","recache") 
		except: pass
		try: self.baseServer_Reader=Config.get("Base Server","reader") 
		except: pass
	
		try: self.logging_File=Config.get("Logging","file") 
		except: pass
		try: self.logging_MaxSize=Config.get("Logging","maxsize") 
		except: pass
		try: self.logging_FileCount=Config.get("Logging","filecount") 
		except: pass
		try: self.logging_UseLog=Config.getboolean("Logging","uselog") 
		except: pass
		try: self.logging_STDOUT=Config.getboolean("Logging","stdout") 
		except: pass