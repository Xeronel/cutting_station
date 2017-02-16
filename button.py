#!/usr/bin/python2.7
import RPi.GPIO as GPIO
from encoder import RotaryEncoder
from time import sleep
from os import system
import socket
import fcntl
import struct


# Setup constants
phase_counter = 0
OK_BUTTON = 4
CANCEL_BUTTON = 17
A_PIN = 22
B_PIN = 23
PREV_SEQ = 0
PREV_DELTA = 1

# Keep track of buttons last state
# button, prev_state
buttons = {
    OK_BUTTON: False,
    CANCEL_BUTTON: False
}

encoder = {
    A_PIN: False,
    B_PIN: False
}

# Channel sound maps
sounds = {
    OK_BUTTON: "success.mp3",
    CANCEL_BUTTON: "error2.mp3"
}

# Configure GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(OK_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(CANCEL_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Events
GPIO.add_event_detect(A_PIN, GPIO.RISING)


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


def counter(channel):
    global phase_counter
    global PREV_DELTA

    phase_counter += PREV_DELTA


def print_wire_length(channel):
    global phase_counter
    feet, counter = divmod(phase_counter, 600)
    inches = counter / 50
    print("Feet %s, Inches: %s" % (feet, inches))


if __name__ == '__main__':
    print(get_ip_address('eth0'))
    try:
        # Setup event listeners
        GPIO.add_event_callback(A_PIN, counter)
        encoder = RotaryEncoder(A_PIN, B_PIN)
        encoder.start()

        while True:
            for button, prev_state in buttons.items():
                pressed = GPIO.input(button)
                if pressed and prev_state is False:
                    print("Counter: %s" % phase_counter)
                    print_wire_length(A_PIN)
                    phase_counter = 0
                    buttons[button] = True
                    beep(button)
                    #print_test(button)
                elif not pressed and prev_state is True:
                    buttons[button] = False

            sleep(0.1)
    except KeyboardInterrupt:
        encoder.stop()
        GPIO.cleanup()
