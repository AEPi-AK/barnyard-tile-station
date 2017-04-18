#!/usr/bin/env python

import time

from pirc522 import RFID
import RPi.GPIO as GPIO

PLAYER_NUM = 2

BUTTON_PIN = 8
BUTTON_LIGHT_PIN = 10
GPIO.setmode(GPIO.BOARD)


GPIO.setup(BUTTON_LIGHT_PIN, GPIO.OUT)

rdr1 = RFID(bus=1, device=0, pin_rst=37, pin_irq=33, pin_ce=12)
rdr2 = RFID(bus=1, device=1, pin_rst=31, pin_irq=29, pin_ce=11)
rdr3 = RFID(bus=1, device=2, pin_rst=5, pin_irq=3, pin_ce=36)
rdrs = [rdr1, rdr2, rdr3]

status_pins = [(21, 23, 19), (15, 13, 16), (24, 26, 22)]
for (r, g, b) in status_pins:
    GPIO.setup(r, GPIO.OUT)
    GPIO.setup(g, GPIO.OUT)
    GPIO.setup(b, GPIO.OUT)
    GPIO.output(r, 0)
    GPIO.output(g, 0)
    GPIO.output(b, 0)


def set_red(i):
    GPIO.output(status_pins[i][0], 1)
    GPIO.output(status_pins[i][1], 0)
    GPIO.output(status_pins[i][2], 0)

def set_green(i):
    GPIO.output(status_pins[i][0], 0)
    GPIO.output(status_pins[i][1], 1)
    GPIO.output(status_pins[i][2], 0)

def set_blue(i):
    GPIO.output(status_pins[i][0], 0)
    GPIO.output(status_pins[i][1], 0)
    GPIO.output(status_pins[i][2], 1)

def set_clear(i):
    GPIO.output(status_pins[i][0], 0)
    GPIO.output(status_pins[i][1], 0)
    GPIO.output(status_pins[i][2], 0)

import requests
from hashlib import md5
import json
def place(player, slot, uid):
    s = ''.join([str(x) for x in uid])
    tileid = md5(s).hexdigest()[0:5]
    url = "http://barnyard-nuc.local/place/" + str(player) + "/" + str(slot) + "/" + tileid
    r = requests.post(url)
    print "Posting to", url, "status code", r.status_code
    if r.status_code == 200: 
        j = json.loads(r.text)
        print(j)
        if j["status"] == "success":
            set_green(slot)
        else:
            set_red(slot)
    else:
        set_blue(slot)


def remove(player, slot):
    url = "http://barnyard-nuc.local/remove/" + str(player) + "/" + str(slot)
    r = requests.post(url)
    print "Posting to", url, "status code", r.status_code
    if r.status_code == 200: 
        set_clear(slot)

def game_running():
    r = requests.get("http://barnyard-nuc.local/gamestate")
    if r.status_code == 200:
        j = json.loads(r.text)
        if j["player" + str(PLAYER_NUM)]['joined'] == True:
            GPIO.output(BUTTON_LIGHT_PIN, 0)
        else:
            GPIO.output(BUTTON_LIGHT_PIN, 1)
        return j["currentPhase"] == "GameInProgress"


def handle_button(channel):
    url = "http://barnyard-nuc.local/join/" + str(PLAYER_NUM)
    r = requests.post(url)
    print "Posting to", url, "status code", r.status_code
    if r.status_code == 200: 
        BUTTON_LIGHT_ON = False
        print("posted player join")

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=handle_button, bouncetime=300)
print("Starting")
def run_game():
    curr_uid = [None, None, None]
    curr_uid_count = [0, 0, 0]
    def has_uid():
        return any([i!=0 for i in curr_uid_count])
    while game_running() or has_uid(): 
        print("poll")
        for i in range(0, 3):
            rdr = rdrs[i]
            (error, data) = rdr.request()
            (error, uid) = rdr.anticoll()
            if not error and curr_uid_count[i] < 2:
                curr_uid_count[i] = 2
            if not error and uid != curr_uid[i] and curr_uid_count[i] == 2:
                curr_uid[i] = uid
                place(PLAYER_NUM, i, uid)
            if error and curr_uid_count[i] > 0:
                curr_uid_count[i] -= 1
            if error and curr_uid[i] != None and curr_uid_count[i] == 0:
                remove(PLAYER_NUM, i)
                curr_uid[i] = None
            time.sleep(.02)

    while not game_running():
        print("no poll")
        time.sleep(0.5)

while True:
    run_game()
