#!/usr/bin/python2.7
import RPi.GPIO as GPIO
from encoder import RotaryEncoder
from time import sleep
from os import system
import socket
import fcntl
import struct


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
GPIO.add_event_detect(A_PIN, GPIO.BOTH)
GPIO.add_event_detect(B_PIN, GPIO.BOTH)


# Global Vars
phase_counter = 0
last_count = 0


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


def counter(channel, encoder):
    global phase_counter
    if encoder.rotation > 0:
        phase_counter += 1
    else:
        phase_counter += -1

    if phase_counter < 0:
        phase_counter = 0


def print_wire_length():
    global phase_counter
    feet, counter = divmod(int(phase_counter), 2400)
    inches = int(counter) / 200
    print("Feet %s, Inches: %s" % (feet, inches))


if __name__ == '__main__':
    encoder = RotaryEncoder(A_PIN, B_PIN)
    print(get_ip_address('eth0'))
    try:
        # Start the encoder
        encoder.start()

        # Setup event listeners
        GPIO.add_event_callback(A_PIN, lambda x: counter(x, encoder))

        while True:
            for button, prev_state in buttons.items():
                pressed = GPIO.input(button)
                if pressed and prev_state is False:
                    print("Counter: %s" % phase_counter)
                    print_wire_length()
                    phase_counter = 0
                    buttons[button] = True
                    beep(button)
                    #print_test_label(button)
                elif not pressed and prev_state is True:
                    buttons[button] = False
            sleep(0.1)
    except KeyboardInterrupt:
        encoder.stop()
        GPIO.cleanup()
