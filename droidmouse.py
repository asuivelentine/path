#!/usr/bin/python3
import sys
import socket
import subprocess
import math
import getpass
import hashlib

try:
	from Crypto.Cipher import AES
	AES_present = True
except ImportError:
	print("PyCrypto not installed, you will not be able to use a secured connection.")
	AES_present = False

# print debug message with "[Debug]"-prefix
def debug(*message):
	if isDebugging:
		print("[Debug] ", end="")
		for i in range(len(message)):
			print(str(message[i]), end=" ")
		print("")

# method to combine two bytes of data to one number
def combine2(byte1, byte2):
	return (byte1 << 8) + byte2

# method to combine three bytes of data to one number
def combine3(byte1, byte2, byte3):
	return (byte1 << 16) + (byte2 << 8) + byte3

# run a command
def run(cmd):
	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	return process.communicate()[0]

# get the dimension of the screen
def get_screen_dim():
	dim = str(run("xdotool getdisplaygeometry"), "UTF-8")
	debug("(get_screen_dim) " + dim.split()[0] + "x" + dim.split()[1])
	return int(dim.split()[0]), int(dim.split()[1])

# get the distance between two points
def distance(v1, v2):
	return math.sqrt(abs(v1) ** 2 + abs(v2) ** 2)

# parse data and execute methods
def parse(data):
	if data[1] == 0x01: # mouse move
		x = combine3(data[4], data[5], data[6])
		y = combine3(data[7], data[8], data[9])
		a = data[10]
		mouse_move(x, y, a, screen_x, screen_y)
	elif data[1] == 0x02: # mouse click
		click_type = data[4] + 1
		mouse_click(click_type)
	elif data[1] == 0x03: # close session
		global MODE
		MODE = "initial"
		debug("Closed Session")
	else: # anything else
		print("[Error] (parse:) Cannot handle CMD value:", hex(data[1]))
		return

# method to move the mouse via xdotool
def mouse_move(percent_x, percent_y, acc, scr_x, scr_y):
	percent_x /= 10000000 # was multiplied before; now we have x.yyyyyyy ; x e {0, 1}; y e {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
	percent_y /= 10000000 # ''
	debug("(mouse_move) %x:", percent_x, "%y:", percent_y, "with speed:", acc)
	
	# rechnerrei
	global last_mouse_x, last_mouse_y
	new_x = (scr_x * percent_x) - last_mouse_x
	new_y = (scr_y * percent_y) - last_mouse_y

	# store actual x and y to last_mouse_x and last_mouse_y
	last_mouse_x += new_x
	last_mouse_y += new_y
	
	# this enables progressive swiping by detecting when the user lifts up the finger and puts it back down farer away
	if (distance(new_x, new_y) > 80):
		new_x = 0
		new_y = 0

	# adjust cmd: (remove "echo" if present)
	cmd = "xdotool mousemove_relative -- " + str(round(new_x)) + " " + str(round(new_y)) # build cmd
	debug("(mouse_move) " + cmd)
	output = run(cmd)
	debug("(mouse_move) (output cmd) " + str(output, "UTF-8"))

# method to click/scroll
def mouse_click(click_type):
	debug("(mouse_click) clicking mouse with type:", click_type)
	cmd = "xdotool click " + str(click_type)
	debug("(mouse_click) " + cmd)
	output = run(cmd)
	debug("(mouse_click) (output cmd) " + str(output, "UTF-8"))

# calc the lenth of the data bytes
def calc_data_len(data):
	debug("Data len:", combine2(data[2], data[3]))
	return combine2(data[2], data[3])

# check if data starts with STX
# and check if check sum equals the calculated one
def check(data):
	if data[0] != 0x00: # STX check
		print("[Error] (check:) Invalid packet, expected 0x00 as STX.")
		return False
	cmdDatLen = calc_data_len(data)
	dataBytes = data[0:4 + cmdDatLen] 
	checkSum  = data[4 + cmdDatLen]
	if checkSum != calc_cs(dataBytes):
		print("[Error] (check:) Invalid checksum, got:", checkSum, "calculated:", calc_cs(dataBytes))
		return False
	else:
		return True

# calculate the check sum
def calc_cs(byteList):
	cs = 0x00
	#debug(byteList)
	for i in range(len(byteList)):
		cs = cs ^ byteList[i]
		#debug("(calc_cs) Checksum: " + str(cs))
	return cs

# tests if a packet is "open session"
def is_open_session(data):
	if data[1] == 0x00:
		return True
	else:
		return False
	
# remove the padding from the message
def depad(s):
	num = s[-1]
	if int(num) > 16 or int(num) > len(s):
		result = bytearray(chr(8) + chr(0) + chr(0) + chr(0) + chr(0) + chr(0), "utf-8") # default faulty message
	else:
		result = s[0:-num]
	return result

# decrypts a packet with AES
def decrypt(data, cipher, key):
	result = depad(cipher.decrypt(data)) # decode??
	return result

# returns True if the packet is a poll request by the client
def isPollRequest(data):
	if data == bytes(chr(0) + chr(4) + chr(0) + chr(0) + chr(4), "UTF-8"):
		print("fuckin poll request")
		return True
	else:
		return False

# --------------------------
# end of function definition
# --------------------------

# toggle debug mode
if len(sys.argv) == 1:
		isDebugging = False
elif len(sys.argv) == 2:
	if len(sys.argv) > 1 and (sys.argv[1] == "-dc" or sys.argv[1] == "-cd"):
		isDebugging = True
		print("[Debug Mode]")
		AES_present = False
		print("[Encryption deactivated]")
	elif len(sys.argv) > 1 and sys.argv[1] == "-d":
		isDebugging = True
		print("[Debug Mode]")
	elif len(sys.argv) > 1 and sys.argv[1] == "-c":
		AES_present = False
		print("[Encryption deactivated]")
		isDebugging = False
	else:
		print("Usage: python3 <serverfile>.py [-c|-d]")
		sys.exit()
elif len(sys.argv) == 3:
	if (sys.argv[1] == "-c" and sys.argv[2] == "-d") or (sys.argv[1] == "-d" and sys.argv[2] == "-c"):
		isDebugging = True
		print("[Debug Mode]")
		AES_present = False
		print("[Encryption deactivated]")
	else:
		print("Usage: python3 <serverfile>.py [-c|-d]")
		sys.exit()
else:
	print("Usage: python3 <serverfile>.py [-c|-d]")
	sys.exit()


# IP and Port to run the server on
UDP_IP = "localhost"
UDP_PORT = 13844

# UDP buffer size
UDP_BUFFER_SIZE = 32

# Server mode
MODE = "initial" # no session is opened
# MODE = "session" # a session is opened

# client address
CLIENT_ADDRESS = ""

# screen dimensions
screen_x, screen_y = get_screen_dim()

# last pos of mouse
last_mouse_x = screen_x / 2;
last_mouse_y = screen_y / 2;

# display own IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
	s.connect(("8.8.8.8", 80))
	print("The IP of this PC is: " + s.getsockname()[0])
	s.close()
except OSError:
	IPofPC = socket.gethostbyname(socket.gethostname())
	if IPofPC == "127.0.0.1" or IPofPC == "127.0.0.2":
		print("Could not show the IP of this PC.")
	else:
		print("The IP of this PC is: " + IPofPC)

# password input
if AES_present:
	try:
		PW = getpass.getpass() # prompt for the password
		md5PW = hashlib.md5() # make a new md5 object
		md5PW.update(bytearray(PW, "utf-8")) # pipe in the raw password
		PW_hash = md5PW.digest() # generate digest
		debug("PW:", PW_hash)
		Cipher = AES.new(PW_hash, AES.MODE_ECB) # create cipher
	except KeyboardInterrupt:
		print("\nExiting...")
		sys.exit()

# bind socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))

# main loop
while True:
	# receive data from socket
	try:
		raw_data, address = sock.recvfrom(UDP_BUFFER_SIZE) # buffer
	except KeyboardInterrupt:
		print("\nExiting...")
		sys.exit()
	
	if MODE == "initial":
		if isPollRequest(raw_data):
			answer_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			answer_sock.sendto(bytes(chr(0) + chr(5) + chr(0) + chr(0) + chr(5), "UTF-8"), address)
			continue

	# show packet if encrypted
	if AES_present:
		debug("Unencrypted packet  :", address, [hex(raw_data[c]) for c in range(len(raw_data))])

	# decrypt data here
	if AES_present:
		data = decrypt(raw_data, Cipher, PW_hash)
	else:
		data = raw_data

	# show packet
	debug("Received packet from:", address, [hex(data[c]) for c in range(len(data))])

	# do magic stuff ;)
	if check(data):
		debug("Check successful")
		if MODE == "initial": # if no session is open, open one
			if is_open_session(data):
				debug("Opening Session")
				MODE = "session"
				CLIENT_ADDRESS = address
				debug("Opened session: ", address)
		elif MODE == "session": # if a session is open, go on as usual
			debug("Currently session open")
			if address[0] == CLIENT_ADDRESS[0] and address[1] == CLIENT_ADDRESS[1]:
				parse(data)
			else:
				debug("Foreign packet! Adress: ", address, " bound address: ", CLIENT_ADDRESS)

