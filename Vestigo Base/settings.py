#!/usr/bin/env python

import os.path
import ConfigParser

class Settings():
	def __init__(self):
		#Set defaults
		self.baseServer_Port=8080
		self.baseServer_ForwardData=None
		self.baseServer_Recache=60
		self.baseServer_ForwardTimeout=8
		self.baseServer_ForwardLocation=True
		
		self.logging_File="vestigo_base.log"
		self.logging_MaxSize=1024*1024 # 1MB
		self.logging_FileCount=5
		self.logging_UseLog=False
		self.logging_STDOUT=True
		
		if not os.path.isfile("vestigo_base.ini"):
			raise "Error reading configuration file"
		
		Config = ConfigParser.ConfigParser()
		Config.read("vestigo_base.ini")
	
		try: self.baseServer_Port=int(Config.get("Base Server","port"))
		except: pass
		try: self.baseServer_ForwardData=Config.get("Base Server","forwarddata") 
		except: pass
		try: self.baseServer_RecacheRules=int(Config.get("Base Server","recacherules"))
		except: pass
		try: self.baseServer_ForwardTimeout=int(Config.get("Base Server","forwardtimeout"))
		except: pass
		try: self.baseServer_ForwardLocation=Config.getboolean("Base Server","forwardlocation")
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