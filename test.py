#!/usr/bin/env python

import time

from pirc522 import RFID
import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BOARD)

rdr1 = RFID(bus=1, device=0, pin_rst=37, pin_irq=33, pin_ce=12)
rdr2 = RFID(bus=1, device=1, pin_rst=31, pin_irq=29, pin_ce=11)
rdr3 = RFID(bus=1, device=2, pin_rst=5, pin_irq=3, pin_ce=36)
rdrs = [rdr1, rdr2, rdr3]

status_pins = [(21, 23), (15, 19), (24, 26)]
for (r, g) in status_pins:
    GPIO.setup(r, GPIO.OUT)
    GPIO.setup(g, GPIO.OUT)
    GPIO.output(r, 0)
    GPIO.output(g, 0)



def set_red(i):
    GPIO.output(status_pins[i][0], 1)
    GPIO.output(status_pins[i][1], 0)

def set_green(i):
    GPIO.output(status_pins[i][1], 1)
    GPIO.output(status_pins[i][0], 0)

def set_clear(i):
    GPIO.output(status_pins[i][0], 0)
    GPIO.output(status_pins[i][1], 0)

import requests
from hashlib import md5
import json
def place(player, slot, uid):
    s = ''.join([str(x) for x in uid])
    tileid = md5(s).hexdigest()[0:5]
    url = "http://barnyard-nuc.local/place/" + str(player) + "/" + str(slot) + "/" + tileid
    r = requests.post(url)
    print("Posting to", url)
    if r.status_code == 200: 
        print("success!")
        j = json.loads(r.text)
        print(j)
        if j["status"] == "success":
            set_green(i)
        else:
            set_red(i)

    else: print("failure")

def remove(player, slot):
    url = "http://barnyard-nuc.local/remove/" + str(player) + "/" + str(slot)
    r = requests.post(url)
    print("Posting to", url)
    if r.status_code == 200: 
        print("success!")
    else: print("failure")
    set_clear(i)



curr_uid = [None, None, None]
curr_uid_count = [0, 0, 0]

print("Starting")
while True:
    for i in range(0, 3):
        rdr = rdrs[i]
        (error, data) = rdr.request()
        (error, uid) = rdr.anticoll()
        if not error and curr_uid_count[i] < 2:
            curr_uid_count[i] = 2
        if not error and uid != curr_uid[i] and curr_uid_count[i] == 2:
            curr_uid[i] = uid
            place(1, i, uid)
        if error and curr_uid_count[i] > 0:
            curr_uid_count[i] -= 1
        if error and curr_uid[i] != None and curr_uid_count[i] == 0:
            remove(1, i)
            curr_uid[i] = None
        time.sleep(.02)
