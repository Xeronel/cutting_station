#!/usr/bin/python2.7
import RPi.GPIO as GPIO
from encoder import RotaryEncoder
from time import sleep
from os import system
import socket
import fcntl
import struct
from sdlgui import GUI
from multiprocessing import Manager, Lock
from ctypes import c_int
from threaded_counter import UpdateCounter


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
phase_count = manager.Value(c_int, 0)
lock = Lock()


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def beep(channel):
    if channel in sounds:
        system('mpg123 -q %s &' % sounds[channel])


def print_test_label(channel):
    system("/usr/bin/lp /home/pi/test.txt")


if __name__ == '__main__':
    encoder = RotaryEncoder(A_PIN, B_PIN)
    gui = GUI(phase_count)
    update_counter = UpdateCounter(lock, phase_count, encoder)

    print(get_ip_address('eth0'))

    try:
        update_counter.start()
        encoder.run()
        gui.start()

        while True:
            for button, prev_state in buttons.items():
                pressed = GPIO.input(button)
                if pressed and prev_state is False:
                    print("Encoder: %s" % encoder.counter)
                    encoder.counter = 0
                    buttons[button] = True
                    beep(button)
                    #print_test_label(button)
                elif not pressed and prev_state is True:
                    buttons[button] = False
            sleep(0.1)
    except KeyboardInterrupt:
        GPIO.cleanup()
