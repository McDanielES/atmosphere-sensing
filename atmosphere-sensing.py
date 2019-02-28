'''
**********************************************************************
* Filename    : atmosphere-sensing.py
* Description : A script run by UW Fox Valley drone fitted with a
*               Raspberry Pi 3B+. This script collects measurable
*               atmospheric data when the drone is in flight.
* Author      : Eric McDaniel - University of Wisconsin - Fox Valley
* E-mail      : mcdae6861@students.uwc.edu
* Website     : https://github.com/McDanielES/atmosphere-sensing
* Version     : 1.3
* Update      : 2/25/19
**********************************************************************
'''

import RPi.GPIO as GPIO
import time
from time import localtime, strftime
import os.path

DHT   = 17  # BCM: 17 (Board: 11)
LED_1 = 27  # BCM: 27 (Board: 13)
LED_2 = 22  # BCM: 22 (Board: 15)
PUD   = 23  # BCM: 23 (Board: 16)

MAX_UNCHANGE_COUNT         = 100
STATE_INIT_PULL_DOWN       = 1
STATE_INIT_PULL_UP         = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP         = 4
STATE_DATA_PULL_DOWN       = 5

def setup():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(LED_1, GPIO.OUT)
	GPIO.output(LED_1, GPIO.LOW)
	GPIO.setup(LED_2, GPIO.OUT)
	GPIO.output(LED_2, GPIO.LOW)
	GPIO.setup(PUD, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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
		print("\tCorrupt Data\t\t   Time: %s Seconds" % (currentTime))
		return False

	shortest_pull_up = min(lengths)
	longest_pull_up  = max(lengths)
	halfway = (longest_pull_up + shortest_pull_up) / 2
	bits = []
	the_bytes = []
	byte = 0

	for length in lengths:
		bit = 0
		if length > halfway:
			bit = 1
		bits.append(bit)
	for i in range(0, len(bits)):
		byte = byte << 1
		if (bits[i]):
			byte = byte | 1
		else:
			byte = byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		print ("\tCorrupt Data\t\t    Time: %s Seconds" % (currentTime))
		return False

	return the_bytes[0], the_bytes[2]


def main():
	# Print general info
	print("Sourced from the SunFounder Electronics Kit,")
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
	GPIO.output(LED_1, GPIO.HIGH)
	if GPIO.input(23) == GPIO.HIGH:
		ready = True
	else:
		print("Flip switch to begin data collection.")
		ready = False

	while not ready:
		if GPIO.input(23) == GPIO.HIGH:
			ready = True
		time.sleep(0.25)

	currentTime = 0

	while (currentTime < 600) and (GPIO.input(23) == GPIO.HIGH):
		currentTime += 1
		corruptCounter = 0
		result = read_dht11_dat(currentTime)
		while (result == False):
			result = read_dht11_dat(currentTime)
			print(corruptCounter)
			corruptCounter += 1

		if result:
			humidity, temperature = result
			print("Humidity: %s%%,  Temperature: %s C, Time: %s Seconds" % (humidity, temperature, currentTime))
			textfile.write("%s, %s, %s\n" % (humidity, temperature, currentTime))
		else:
			textfile.write("-1, -1, %s\n" % (currentTime))

		# Oscillate the LED on/off to indicate each file write
		GPIO.output(LED_2, GPIO.HIGH)
		time.sleep(0.5)
		GPIO.output(LED_2, GPIO.LOW)
		time.sleep(0.45)
	
	textfile.close
	print("Done. Normal Termination.")
	
	# Cleanup GPIO, turn off LEDs.
	destroy()

def destroy():
	GPIO.cleanup()

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		destroy()