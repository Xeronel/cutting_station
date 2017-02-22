#!/usr/bin/python2.7
import RPi.GPIO as GPIO
from encoder import RotaryEncoder
import os
import socket
import fcntl
import struct
from sdlgui import GUI
from multiprocessing import Manager, Lock, Pipe
from ctypes import c_char_p
from inputs import Inputs


# Setup constants
OK_BUTTON = 4
CANCEL_BUTTON = 17
A_PIN = 22
B_PIN = 23

# Keep track of buttons last state
# button, prev_state
buttons = {
    OK_BUTTON: False,
    CANCEL_BUTTON: False
}

# Channel sound maps
sounds = {
    OK_BUTTON: "sound/success.mp3",
    CANCEL_BUTTON: "sound/error.mp3"
}

# Configure GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(OK_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(CANCEL_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Events
GPIO.add_event_detect(A_PIN, GPIO.FALLING)
GPIO.add_event_detect(B_PIN, GPIO.FALLING)

# Global Vars
manager = Manager()
length = manager.Value(c_char_p, "Feet: 0, Inches: 0")
lock = Lock()


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


if __name__ == '__main__':
    enc_pipe1, enc_pipe2 = Pipe()

    inputs = Inputs(OK_BUTTON, CANCEL_BUTTON, buttons, sounds, length, lock)
    encoder = RotaryEncoder(A_PIN, B_PIN, OK_BUTTON, CANCEL_BUTTON, enc_pipe2)
    gui = GUI(length)

    print(get_ip_address('eth0'))
    print("Main: %s" % os.getpid())

    try:
        encoder.start()
        inputs.start()
        gui.start()

        while True:
            inputs.add_count(enc_pipe1.recv())

    except KeyboardInterrupt:
        GPIO.cleanup()

