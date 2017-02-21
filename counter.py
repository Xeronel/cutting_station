#!/usr/bin/python2.7
import RPi.GPIO as GPIO
from encoder import RotaryEncoder, RotaryEncoderProcess
from time import sleep
import os
from os import system
import socket
import fcntl
import struct
from sdlgui import GUI
from multiprocessing import Manager, Lock, Pipe
from ctypes import c_int, c_char_p
from threaded_counter import UpdateCounter
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


def print_test_label(channel):
    system("/usr/bin/lp /home/pi/test.txt")


if __name__ == '__main__':
    #update_counter = UpdateCounter(lock, phase_count, encoder)

    enc_pipe1, enc_pipe2 = Pipe()
    gui_pipe1, gui_pipe2 = Pipe()

    inputs = Inputs(buttons, sounds, gui_pipe1)
    encoder = RotaryEncoderProcess(A_PIN, B_PIN, enc_pipe2)
    gui = GUI(gui_pipe2)

    print(os.getpid())
    print(get_ip_address('eth0'))

    try:
        #update_counter.start()
        #inputs.start()
        encoder.start()
        inputs.start()
        gui.start()

        while True:
            inputs.add_count(enc_pipe1.recv())

    except KeyboardInterrupt:
        GPIO.cleanup()

