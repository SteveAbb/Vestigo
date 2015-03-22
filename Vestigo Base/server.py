#!/usr/bin/env python

import thread
import time
from settings import Settings
import requests
import json
from logger import Logger
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs
from SocketServer import ThreadingMixIn
import threading
from threading import Timer
import collections
import copy

class Server():
	def __init__(self,settings,logger):
		self.assetToPayload={}
		self._logger=logger
		self._settings=settings
		self._lastFetchLocations=None
		self._lastFetchAddresses=None
		self._locations=None
		self._addresses=None
		self._addressToTimer = {}
		self._server = VestigoHTTPServer(("", self._settings.baseServer_Port), HTTPHandler, self.log,self.processPayload,self.getAddresses,self.assetToPayload)
	
	def processPayload(self, payload):
		
		lastLocation = None;
		
		if(self._settings.baseServer_ForwardLocation):
			if(payload["address"] in self.assetToPayload and "location" in self.assetToPayload[payload["address"]]):
				lastLocation = self.assetToPayload[payload["address"]]["location"]
		
		if("outofrange" in payload and payload["outofrange"]):
			self.log("Timeout timer elapsed. Moving " + payload["name"] + " into location: out of range.");
			payload["location"]="out of range";
			payload.pop("outofrange",None);
		else:
			ruleMatches=False	
			for location in self.getLocations():
				for rule in self.getLocations(location):
					if(rule["reader"]==payload["reader"]):
						if(payload["address"] in self.getAddresses("nonDisc")):
							if(int(payload["rssi"])>=int(rule["grpr"]["min"]) and int(payload["rssi"])<=int(rule["grpr"]["max"])):
								ruleMatches=True
						else:
							if(int(payload["rssi"])>=int(rule["rssi"]["min"]) and int(payload["rssi"])<=int(rule["rssi"]["max"])):
								ruleMatches=True

					if(ruleMatches):
						self.log("Name: "+payload["name"]+" is in location: "+location)
						payload["location"]=location
						break
				if(ruleMatches):
					break

			if(ruleMatches and "timeout" in self.getAddresses("all")[payload["address"]]):
				if(payload["address"] in self._addressToTimer):
					
					self.log("Reseting timeout timer for " + payload["name"]);
					self._addressToTimer[payload["address"]].cancel();
				else:
					self.log("Starting timer for " + payload["name"] + " for " + str( self.getAddresses("all")[payload["address"]]["timeout"]) + " seconds.");
					
				timerPayload = copy.deepcopy(payload);
				timerPayload["rssi"] = 0
				timerPayload["reader"] = ""
				timerPayload["outofrange"] = True;

				timer = Timer(self.getAddresses("all")[payload["address"]]["timeout"], self.processPayload, (timerPayload,));

				self._addressToTimer[payload["address"]] = timer
				self._addressToTimer[payload["address"]].start()
		
		self.assetToPayload[payload["address"]]=payload;
		
		if(self._settings.baseServer_ForwardData is not None):
			if(self._settings.baseServer_ForwardLocation):
				if("location" not in payload or "location" in payload and lastLocation == payload["location"]):
					return
			self.log("Forwarding payload off to: "+self._settings.baseServer_ForwardData)
			try:
				self.log("Forward Payload: ")
				self.log(json.dumps(payload,indent=4))
				headers = {'content-type': 'application/json'}
				resp = requests.post(self._settings.baseServer_ForwardData, data=json.dumps(payload), headers=headers,timeout=int(self._settings.baseServer_ForwardTimeout))
				self.log("Resp: "+str(resp.status_code))
			except Exception, error:
				self.log("Error with forward request: "+str(error))	
	
	def getAddresses(self,type=None):
		fetchNew=False
		if(self._lastFetchAddresses is not None):
			if((time.time()-self._lastFetchAddresses)>int(self._settings.baseServer_Recache)):
				fetchNew=True
		else:
			fetchNew=True
		
		if(fetchNew):
			try:
				self._lastFetchAddresses=time.time()
				self.log("Recaching addresses.")
				f = open("addresses.cfg")
				self._addresses=json.loads(f.read())
				f.close()
				self.log("Finished recache.")
			except Exception,error:
				self.log("Error rechaching addresses: "+str(error)+". Will retry on next recache.")
				
		if(type is None):	
			return self._addresses
		elif(type is "all"):
			return dict(self._addresses["ble"].items() + self._addresses["disc"].items()+self._addresses["nonDisc"].items())
		else:
			return self._addresses[type]
			
	def getLocations(self,location=None):
		fetchNew=False
		if(self._lastFetchLocations is not None):
			if((time.time()-self._lastFetchLocations)>int(self._settings.baseServer_Recache)):
				fetchNew=True
		else:
			fetchNew=True
		
		if(fetchNew):
			try:
				self._lastFetchLocations=time.time()
				self.log("Recaching locations.")
				f = open("locations.cfg")
				self._locations=json.loads(f.read(),object_pairs_hook=collections.OrderedDict)
				f.close()
				self.log("Finished recache.")
			except Exception,error:
				self.log("Error rechaching locations: "+str(error)+". Will retry on next recache.")
		if location is None:
			return self._locations
		else:
			return self._locations[location]
	
	def log(self,data):
		self._logger.log(data)
		
	def start(self):
		self.log("Base server starting on port: "+str(self._settings.baseServer_Port))
		self._server.serve_forever()
	
	def stop(self):
		self.log("Base server shutting down...")
		self._server.shutdown()
		self.log("Killing all timers.");
		for key in self._addressToTimer:
			try:
				self._addressToTimer[key].cancel();
			except: 
				pass

class VestigoHTTPServer(ThreadingMixIn, HTTPServer):
	def __init__(self, server_address, RequestHandlerClass, log, processPayload,getAddresses,assetToPayload):
		HTTPServer.__init__(self, server_address, RequestHandlerClass)
		self.log = log
		self.processPayload=processPayload
		self.getAddresses=getAddresses
		self.assetToPayload=assetToPayload
		
class HTTPHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		dirs=self.path.split("/")
		if(len(dirs)>1):
			resource=dirs[1]
			if(resource == "addresses"):
				try:
					queryStr=parse_qs(urlparse(self.path).query)
					reader=str(queryStr["reader"][0])
					self.send_response(200)
					self.send_header('Content-type',"application/json")
					self.end_headers()
					self.wfile.write(json.dumps(self.server.getAddresses()))
				except IOError as e:
					self.send_response(404)
					self.server.log("Error with processing readers request for addresses: "+str(e))
			elif(resource == "states"):
				try:
					self.send_response(200)
					self.send_header('Content-type','application/json')
					self.end_headers()
					self.wfile.write(json.dumps(self.server.assetToPayload.values()))
				except IOError as e:
					self.send_response(404)
					self.server.log("Error with processing request for asset states: "+str(e))
			else:
				fileName="web/view.html"
				contentType="text/html"
				if("style.css" in dirs):
					fileName="web/style.css"
					contentType="text/css"
				elif("coords.cfg" in dirs):
					fileName="web/coords.cfg"
					contentType="application/json"
				elif("blueprint.png" in dirs):
					fileName="web/blueprint.png"
					contentType="image/png"
				elif("coord.html" in dirs):
					fileName="web/coord.html"
					contentType="text/html"
				elif("logo.png" in dirs):
					fileName="web/logo.png"
					contentType="image/png"
				f = open(fileName)
				self.send_response(200)
				self.send_header('Content-type',contentType)
				self.end_headers()
				self.wfile.write(f.read())
				f.close()
		else:
			self.send_response(404)
			self.server.log("Error with request. No resource specified")
			
	def do_POST(self):
		try:
			self.server.log("Asset data recieved from a reader.")
			content_len = int(self.headers.getheader('content-length'))
			request_data = self.rfile.read(content_len)
			self.send_response(200)
			self.server.log("Attempting to parse request content.")
			payload=json.loads(request_data)
			self.server.log("Payload recieved: ")
			self.server.log(json.dumps(payload,indent=4))
			self.server.processPayload(payload)
		except Exception, error:
			self.send_response(404)
			self.server.log("Error with payload request from reader: "+str(error))
	
	def log_message(self, format, *args):
		return