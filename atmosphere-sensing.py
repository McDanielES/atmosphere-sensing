'''
**********************************************************************
* Filename    : dht11.py
* Description : test for SunFoudner DHT11 humiture & temperature module
* Author      : Dream
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Dream    2016-09-30    New release
**********************************************************************
'''
import RPi.GPIO as GPIO
import time
from time import gmtime, strftime

DHTPIN = 17

GPIO.setmode(GPIO.BCM)

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

def read_dht11_dat(currentTime):
	GPIO.setup(DHTPIN, GPIO.OUT)
	GPIO.output(DHTPIN, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(DHTPIN, GPIO.LOW)
	time.sleep(0.02)
	GPIO.setup(DHTPIN, GPIO.IN, GPIO.PUD_UP)
	
	unchanged_count = 0
	last = -1
	data = []
	while True:
		current = GPIO.input(DHTPIN)
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
	print ("Sourced from the SunFounder Electronis Kit,\nRaspberry Pi wiringPi DHT11 Temperature program.\nModified by Eric McDaniel for undergraduate research on a RPi-fitted drone.\n")
	currentTime = 0
	fileCurrentTime = "/home/pi/Desktop/DroneTestData/Humid-Temp-"+ strftime("%m-%d-%Y_%H:%M:%S", gmtime()) + ".txt"
	
	GPIO.setwarnings(False)
#	Setup GPIO with pin layout for pull down switch
#	Activate Green LED_1 that file is ready to write, Pull Up
	
#	Replace Whle true loop with:
#	While (currentTime < 600) AND (Switch is pulled down)
	while (True):
		currentTime += 1
		time.sleep(1)		# Time will eventually need to be modified to accomodate LED_1 strobe
		result = read_dht11_dat(currentTime)
		if result:
			humidity, temperature = result
			print ("Humidity: %s %%,  Temperature: %s C, Time: %s Seconds" % (humidity, temperature, currentTime))
			
#	It's embarassing how much I could have simplified this...

			text_file = open(fileCurrentTime, "a")
			text_file.write("%s, %s, %s\n" % (humidity, temperature, currentTime))
			text_file.close
		else:
			text_file = open(fileCurrentTime, "a")
			text_file.write("-1, -1, %s\n" % (currentTime))
			text_file.close
#		Strobe LED_1 here
	print("Done. Normal Termination. Ten minutes have elapsed.")
	
#	Activate Red LED_2 to indicate program terminated
        

def destroy():
	GPIO.cleanup()

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		destroy() 
