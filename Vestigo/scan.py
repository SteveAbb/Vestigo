#!/usr/bin/env python

import pexpect
import subprocess
import thread
from multiprocessing.pool import ThreadPool
import time
from settings import Settings
import requests
import json
from logger import Logger

class Scanner():
	def __init__(self,settings,logger):
		self._logger=logger
		self._bleScanProc = None
		self._scanProc=None
		self._addrToRssi={}
		self._keepScanning=True
		self._settings=settings
		self._lastFetch=None
		self._nonDiscKeepScanning=True
		self._addresses=None
	
	def log(self,data):
		self._logger.log(data)
			
	def getAddresses(self,type=None):
		fetchNewAssets=False
		if(self._lastFetch is not None):
			if((time.time()-self._lastFetch)>int(self._settings.baseServer_Recache)):
				fetchNewAssets=True
		else:
			fetchNewAssets=True
		
		if(fetchNewAssets):
			try:
				self._lastFetch=time.time()
				self.log("Recaching")
				resp=requests.get(self._settings.baseServer_URL+"/addresses/?reader="+self._settings.baseServer_Reader,timeout=int(self._settings.baseServer_Timeout))
				self._addresses=resp.json()
				self.log("Finished recache.")
				self._nonDiscKeepScanning=False
			except Exception,error:
				self.log("Error rechaching addresses: "+str(error)+". Will retry on next recache.")
		
		if(type is None):	
			return self._addresses
		elif(type is "all"):
			return dict(self._addresses["ble"].items() + self._addresses["disc"].items()+self._addresses["nonDisc"].items())
		else:
			return self._addresses[type]

	def send_payload(self,addr,rssi):
		if(addr in self.getAddresses("all")):
			self._addrToRssi[addr]=rssi;
			if(addr in self.getAddresses("ble")):
				type="BLE"
			elif(addr in self.getAddresses("disc")):
				type="Discoverable"
			else:
				type="Non-Discoverable"
		
			if((type=="BLE" and self._settings.scanMode_LE) or (type=="Discoverable" and self._settings.scanMode_Disc) or (type=="Non-Discoverable" and self._settings.scanMode_NonDisc)):
				try:
					payload={"reader":self._settings.baseServer_Reader,"name":self.getAddresses("all")[addr]["name"],"address":addr,"rssi":rssi,"type":type}
					self.log("Sending payload to: "+self._settings.baseServer_URL)
					self.log("Payload:")
					self.log(json.dumps(payload,indent=4))
					headers = {'content-type': 'application/json'}
					resp = requests.post(self._settings.baseServer_URL, data=json.dumps(payload), headers=headers,timeout=int(self._settings.baseServer_Timeout))
					self.log("Resp: "+str(resp.status_code))
				except Exception, error:
					self.log("Error with request: "+str(error))
		
	def scanProcessSpawner(self):
		while self._keepScanning:
			self._scanProc = subprocess.Popen(['hcitool', 'scan'],cwd='/usr/bin',stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
			self._scanProc.wait()
			if(self._settings.readTimeout_Disc>0):
				time.sleep(self._settings.readTimeout_Disc)
	
	def nonDiscScanProcessSpawner(self,addr):
		while (self._nonDiscKeepScanning):
			result=pexpect.run("hcitool rssi "+addr,timeout=None)
			if "RSSI return value:" not in result:
				pexpect.run("hcitool cc "+addr,timeout=None)
			else:
				rssi=result.rstrip().split(": ")[1]
			
				if(addr in self._addrToRssi):
					if (rssi!=self._addrToRssi[addr]):
						self.send_payload(addr,rssi)
				else:
					self.send_payload(addr,rssi)
				if(self._settings.readTimeout_NonDisc>0):
					time.sleep(self._settings.readTimeout_NonDisc)
		
	def nonDiscScanPoolInitiate(self):
		pool = ThreadPool(processes=10)
		while self._keepScanning:
			self.log("Mapping non-discoverable addresses to thread pool executors")
			self._nonDiscKeepScanning=True
			pool.map(self.nonDiscScanProcessSpawner, self.getAddresses("nonDisc").keys())
			
	def bleScanProccessSpawnerAsync(self):
		self._bleScanProc = subprocess.Popen(['hcitool', 'lescan', '--duplicates'],cwd='/usr/bin',stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
		
	def parseHcidump(self):
		self.log("Starting parse of hcidump stdout")
		child=pexpect.spawn("hcidump",timeout=None)
		while self._keepScanning:
			child.expect("(([0-9A-F]{2}[:-]){5}([0-9A-F]{2}))",timeout=None)
			addr=child.after
			if (addr in self.getAddresses("nonDisc")):
				continue
			child.expect("(-\d{2})",timeout=None)
			rssi=child.after
	
			if(addr in self._addrToRssi):
				if (rssi!=self._addrToRssi[addr]):
					self.send_payload(addr,rssi)
			else:
				self.send_payload(addr,rssi)
				
	def StartScanning(self):
		self.log(json.dumps(self.getAddresses(), indent=4))
		if(self._settings.scanMode_LE):
			self.log("Spawning BLE scan child proccess")
			self.bleScanProccessSpawnerAsync()
		if(self._settings.scanMode_Disc):
			self.log("Spawning discoverable child process")
			thread.start_new_thread (self.scanProcessSpawner, ())
		if(self._settings.scanMode_NonDisc):
			self.log("Initiating thread pool for non discoverable addresses")
			thread.start_new_thread (self.nonDiscScanPoolInitiate, ())
		self.parseHcidump()
				
	def StopScanning(self):
		self._keepScanning=False
		if(self._settings.scanMode_LE):
			self.log("Killing low energy scan child process")
			self.log(self._bleScanProc.pid)
			try: self._bleScanProc.terminate()
			except(OSError): pass
			self.log("Killed.")
		if(self._settings.scanMode_Disc):
			self.log("Killing normal scan child process")
			self.log(self._scanProc.pid)
			try: self._scanProc.terminate() 
			except(OSError): pass
			self.log("Killed.")