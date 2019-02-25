'''
**********************************************************************
* Filename    : atmosphere-sensing.py
* Description : A script run by UW Fox Valley drone fitted with a
*               Raspberry Pi 3B+. This script collects measurable
* 				atmospheric data when the drone is in flight.
* Author      : Eric McDaniel - University of Wisconsin - Fox Valley
* E-mail      : MCDAE6861@students.uwc.edu
* Website     : https://github.com/McDanielES
* Version     : 1.1
* Update      : 1/10/19
**********************************************************************
'''

import sys


import RPi.GPIO as GPIO
import time
from time import localtime, strftime
import os.path

DHT   = 17  # BCM is 17, Board is 11
LED_1 = 27  # BCM is 27, Board is 13
LED_2 = 22  # BCM is 22, Board is 15

GPIO.setmode(GPIO.BCM)    # Move this to setup?

MAX_UNCHANGE_COUNT 		   = 100
STATE_INIT_PULL_DOWN 	   = 1
STATE_INIT_PULL_UP 		   = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP 		   = 4
STATE_DATA_PULL_DOWN 	   = 5

def setup():
	GPIO.setmode(GPIO.BCM)      # Numbers GPIOs by physical location
	GPIO.setup(LED_1, GPIO.OUT)   # Set LED_1's mode is output
	GPIO.output(LED_1, GPIO.HIGH) # Set LED_1 high(+3.3V) to off led
	GPIO.setup(LED_2, GPIO.OUT)   # Set LED_2's mode is output
	GPIO.output(LED_2, GPIO.HIGH) # Set LED_2 high(+3.3V) to off led
#	GPIO.setwarnings(False) # Previously in main()

def read_dht11_dat(currentTime):
	GPIO.setup(DHT, GPIO.OUT)
	GPIO.output(DHT, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(DHT, GPIO.LOW)
	time.sleep(0.02)
	GPIO.setup(DHT, GPIO.IN, GPIO.PUD_UP)
	
	unchanged_count = 0
	last = -1
	data = []
	while True:
		current = GPIO.input(DHT)
		data.append(current)
		if last != current:
			unchanged_count = 0
			last = current
		else:
			unchanged_count += 1
			if unchanged_count > MAX_UNCHANGE_COUNT:
				break

	state = STATE_INIT_PULL_DOWN

	lengths = []
	current_length = 0

	for current in data:
		current_length += 1

		if state == STATE_INIT_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_INIT_PULL_UP
			else:
				continue
		if state == STATE_INIT_PULL_UP:
			if current == GPIO.HIGH:
				state = STATE_DATA_FIRST_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_FIRST_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_DATA_PULL_UP
			else:
				continue
		if state == STATE_DATA_PULL_UP:
			if current == GPIO.HIGH:
				current_length = 0
				state = STATE_DATA_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_PULL_DOWN:
			if current == GPIO.LOW:
				lengths.append(current_length)
				state = STATE_DATA_PULL_UP
			else:
				continue
	if len(lengths) != 40:
		print ("\tCorrupt Data\t\t    Time: %s Seconds" % (currentTime))
		return False

	shortest_pull_up = min(lengths)
	longest_pull_up = max(lengths)
	halfway = (longest_pull_up + shortest_pull_up) / 2
	bits = []
	the_bytes = []
	byte = 0

	for length in lengths:
		bit = 0
		if length > halfway:
			bit = 1
		bits.append(bit)
#	print ("bits: %s, length: %d" % (bits, len(bits)))
	for i in range(0, len(bits)):
		byte = byte << 1
		if (bits[i]):
			byte = byte | 1
		else:
			byte = byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0
#	print (the_bytes)
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		print ("\tCorrupt Data\t\t    Time: %s Seconds" % (currentTime))
		return False

	return the_bytes[0], the_bytes[2]


def main():
	# Print general info
	print("Sourced from the SunFounder Electronis Kit,")
	print("Raspberry Pi wiringPi DHT11 Temperature program.")
	print("Modified by Eric McDaniel for undergraduate research on a RPi-fitted drone.\n")
	setup()

	# Concatenate the parent/child directories with file name
	currentDir = os.path.dirname(os.path.realpath(__file__))
	originPath = os.path.join(currentDir, "flight-test-data")
	filename = "HumidityTemp_" + strftime("%m-%d-%Y_%H:%M:%S_%p", localtime()) + ".txt"
	filepath = os.path.join(originPath, filename)

	# Create child directory if none exists
	if not os.path.exists(originPath):
		os.mkdir(os.path.join(originPath))

	# Open this file as append mode
	textfile = open(filepath, "a")

	# Script is loaded, file is opened. Illuminate LED to notify user that
	# drone is ready, don't start until the switch is activated
#	Setup GPIO with pin layout for pull down switch
#	GPIO.output(LedPin, GPIO.LOW)	# On?
	ready = True #Temp for False
	while not ready:
		# if(Button is pressed)
			# ready = True
		# BUTTON is not pressed
		time.sleep(0.05)	
	
#	Activate Green LED_1 that file is ready to write, Pull Up
	currentTime = 0

#	While (currentTime < 600) AND (Switch is pulled down)
	while (True):
		currentTime += 1
		
		result = read_dht11_dat(currentTime)
		if result:
			humidity, temperature = result
			print ("Humidity: %s%%,  Temperature: %s C, Time: %s Seconds" % (humidity, temperature, currentTime))
			textfile.write("%s, %s, %s\n" % (humidity, temperature, currentTime))
		else:
			textfile.write("-1, -1, %s\n" % (currentTime))

		# oscilate the LED on/off to indicate each file write
#		GPIO.output(LedPin, GPIO.HIGH)
		time.sleep(0.5)
#		GPIO.output(LedPin, GPIO.LOW)
		time.sleep(0.45)
	
	textfile.close
	print("Done. Normal Termination.")
	
	# Activate red LED to indicate that program is done
#	GPIO.output(LED_2, GPIO.LOW)	# On?
        

def destroy():
	GPIO.cleanup()

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		destroy() 
		pass