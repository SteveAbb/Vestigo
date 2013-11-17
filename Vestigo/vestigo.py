#!/usr/bin/env python

from settings import Settings
from scan import Scanner
from logger import Logger

def main():
	try:
		#Read config file
		settings=Settings()
	
		#Set up logger
		logger=Logger(settings)

		#Create scanner
		scanner=Scanner(settings,logger)

		#Begin scanning
		scanner.StartScanning()
		
	except KeyboardInterrupt:
		scanner.StopScanning()
	
if __name__ == "__main__":
	main()
		
	