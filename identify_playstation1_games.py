#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2015, Matthew Brennan Jones <matthew.brennan.jones@gmail.com>
# A module for identifying Sony Playstation 1 games with Python 2 & 3
# It uses a MIT style license
# It is hosted at: https://github.com/workhorsy/identify_playstation1_games
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import sys, os
import re
import json
import iso9660

IS_PY2 = sys.version_info[0] == 2

BUFFER_SIZE = 1024 * 1024 * 10
MAX_PREFIX_LEN = 6

# All possible serial number prefixes
# Sorted by the number of games that use that prefix
PREFIXES = [
	'SLPS', # 3955 games
	'SLES', # 2413 games
	'SCES', # 2262 games
	'SLPM', # 1695 games
	'SLUS', # 1337 games
	'SCPS', # 484 games
	'SCUS', # 389 games
	'SCED', # 165 games
	'LSP', # 108 games
	'PCPX', # 62 games
	'PAPX', # 54 games
	'SLED', # 53 games
	'SIPS', # 29 games
	'PBPX', # 11 games
	'SLKA', # 4 games
	'SCPM', # 3 games
	'ESPM', # 3 games
	'SLBM', # 1 game
	'SPUS', # 1 game
	'PCPD', # 1 game
	'SLEH', # 1 game
]

# Load the databases
with open('db_playstation1_official_us.json', 'rb') as f:
	db_playstation1_official_us = json.loads(f.read().decode('utf8'))


# Convert the keys from strings to bytes
dbs = [
	db_playstation1_official_us,
]
for db in dbs:
	keys = db.keys()
	for key in keys:
		# Get the value
		val = db[key]

		# Remove the unicode key
		db.pop(key)

		# Add the bytes key and value
		if IS_PY2:
			db[bytes(key)] = val
		else:
			db[bytes(key, 'utf-8')] = val


def _find_in_binary(file_name):
	f = open(file_name, 'rb')
	file_size = os.path.getsize(file_name)
	while True:
		# Read into the buffer
		rom_data = f.read(BUFFER_SIZE)

		# Check for the end of the file
		if not rom_data:
			return None

		# Move back the length of the prefix
		# This is done to stop the serial number from being spread over multiple buffers
		pos = f.tell()
		use_offset = False
		if pos > MAX_PREFIX_LEN and pos < file_size:
			use_offset = True

		# Check if the prefix is in the buffer
		for prefix in PREFIXES:
			m = re.search(prefix + b"[\_|\-][\d|\.]+\;", rom_data)
			if m and m.group() and b'999.99' not in m.group():
				# Get the serial number location
				serial_number = m.group().replace(b'.', b'').replace(b'_', b'-').replace(b';', b'')
				#print('serial_number', serial_number)

				return serial_number

		if use_offset:
			f.seek(pos - MAX_PREFIX_LEN)

	return None


def get_playstation1_game_info(file_name):
	# Skip if not an ISO
	if not os.path.splitext(file_name)[1].lower() in ['.iso', '.bin']:
		raise Exception("Not an ISO or BIN file.")

	disc_type = None
	entries = []

	# Look at each file in the CD ISO
	try:
		if not disc_type:
			cd = iso9660.ISO9660(file_name)
			for sub_entry in cd.tree():
				entries.append(sub_entry.lstrip('/'))
			disc_type = 'CD'
	except:
		pass

	# Look at the entire binary
	if not disc_type:
		entries = [_find_in_binary(file_name)]
		disc_type = 'Binary'

	# Not a supported format
	if not disc_type:
		raise Exception("Failed to read as a CD ISO, or Binary.")

	for sub_entry in entries:

		# Sanitize the file name with the serial number
		serial_number = sub_entry.upper().replace(b'.', b'').replace(b'_', b'-')

		# Skip if the serial number has an invalid prefix
		if serial_number.split(b'-')[0] not in PREFIXES:
			continue

		# Look up the proper name
		title, region = None, None
		'''
		if serial_number in db_playstation1_official_as:
			region = "Asia"
			title = db_playstation1_official_as[serial_number]
		elif serial_number in db_playstation1_official_au:
			region = "Australia"
			title = db_playstation1_official_au[serial_number]
		elif serial_number in db_playstation1_official_eu:
			region = "Europe"
			title = db_playstation1_official_eu[serial_number]
		elif serial_number in db_playstation1_official_jp:
			region = "Japan"
			title = db_playstation1_official_jp[serial_number]
		elif serial_number in db_playstation1_official_ko:
			region = "Korea"
			title = db_playstation1_official_ko[serial_number]
		'''
		if serial_number in db_playstation1_official_us:
			region = "USA"
			title = db_playstation1_official_us[serial_number]

		# Skip if unknown serial number
		if not title or not region:
			continue

		return {
			'serial_number' : serial_number,
			'region' : region,
			'title' : title,
			'disc_type' : disc_type
		}

	raise Exception("Failed to find game in database.")



		