#!/usr/bin/python2.7
import fcntl
import os
import signal
import socket
import struct
import RPi.GPIO as GPIO
from ctypes import c_char_p
from multiprocessing import Manager, Lock, Pipe
from cuttingstation import CuttingStation, RotaryEncoder, GUI


# GPIO inputs
OK_BUTTON = 4
CANCEL_BUTTON = 17
REPRINT_BUTTON = 27
A_PIN = 22
B_PIN = 23

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(OK_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(CANCEL_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(REPRINT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# GPIO Events
GPIO.add_event_detect(A_PIN, GPIO.FALLING)
GPIO.add_event_detect(B_PIN, GPIO.FALLING)

# Shared memory for gui and counter
manager = Manager()
length = manager.Value(c_char_p, "Feet: 0, Inches: 0")
lock = Lock()

# Exit handler
running = True


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def stop(signum, frame):
    global running
    running = False


def cleanup():
    # Exit encoder
    enc_pipe1.send('exit')
    enc_pipe1.close()
    enc_pipe2.close()
    # Exit counter
    cut_station.terminate()
    # Exit GUI
    gui.terminate()
    GPIO.cleanup()


if __name__ == '__main__':
    enc_pipe1, enc_pipe2 = Pipe()

    cut_station = CuttingStation(OK_BUTTON, CANCEL_BUTTON, REPRINT_BUTTON, length, lock)
    encoder = RotaryEncoder(A_PIN, B_PIN, OK_BUTTON, CANCEL_BUTTON, enc_pipe2)
    gui = GUI(length)

    # Handle exit gracefully
    signal.signal(signal.SIGTERM, stop)

    print(get_ip_address('eth0'))
    print("Main: %s" % os.getpid())

    try:
        encoder.start()
        cut_station.start()
        gui.start()

        while running:
            if enc_pipe1.poll(0.1):
                cut_station.update_count(enc_pipe1.recv())

        cleanup()
    except KeyboardInterrupt:
        cleanup()

