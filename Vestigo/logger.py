#!/usr/bin/env python

from settings import Settings
import logging
import logging.handlers
import time

class Logger():
	def __init__(self,settings):
		self._logFile=settings.logging_File
		self._logger = logging.getLogger('vestigo')
		self._logger.setLevel(logging.DEBUG)
		self._settings=settings
		handler = logging.handlers.RotatingFileHandler(self._logFile, maxBytes=1024*int(settings.logging_MaxSize), backupCount=int(settings.logging_FileCount))

		self._logger.addHandler(handler)

	def log(self,data):
		data="["+time.strftime('%X %x')+"] "+str(data)
		if(self._settings.logging_STDOUT):
			print data
		if(self._settings.logging_UseLog):
			self._logger.debug(data)