#!/usr/bin/env python

from settings import Settings
from server import Server
from logger import Logger

def main():
	try:
		#Read config file
		settings=Settings()
	
		#Set up logger
		logger=Logger(settings)

		#Create scanner
		server=Server(settings,logger)

		#Begin scanning
		server.start()
		
	except KeyboardInterrupt:
		server.stop()
	
if __name__ == "__main__":
	main()
		
	