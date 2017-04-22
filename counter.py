#!/usr/bin/python2.7
import logging
import fcntl
import os
import signal
import socket
import struct
import RPi.GPIO as GPIO
from ctypes import c_char_p
from multiprocessing import Manager, Lock
from cuttingstation import CuttingStation, GUI, WebClient, Config
from serial import Serial, SerialException
from serial.tools import list_ports
from systemd import journal
from time import sleep


os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(os.path.abspath(__file__))
config = Config()

# Setup logging facilities
logging.basicConfig(format="[%(filename)s:%(lineno)s %(module)s.%(funcName)s()] %(message)s")
log = logging.getLogger()
log.propagate = True
if config.debug:
    log.setLevel(logging.DEBUG)
else:
    log.addHandler(journal.JournaldLogHandler())
    log.setLevel(logging.INFO)

# GPIO inputs
OK_BUTTON = 4
CANCEL_BUTTON = 17
REPRINT_BUTTON = 27
RESET_PIN = 2

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(OK_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(CANCEL_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(REPRINT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RESET_PIN, GPIO.OUT, initial=GPIO.LOW)

# Shared memory for gui and counter
manager = Manager()
length = manager.Value(c_char_p, "Feet: 0, Inches: 0")
lock = Lock()

# Exit handler
running = True


def get_encoder():
    com_ports = list_ports.comports()
    if com_ports:
        port = com_ports[0][0]
        try:
            return Serial(port, 9600, timeout=1)
        except SerialException:
            return None


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
    cut_station.terminate()
    gui.terminate()
    GPIO.cleanup()


if __name__ == '__main__':
    web_client = WebClient()
    web_client.start()
    while True:
        sleep(0.1)

if __name__ == '__derp__':
    cut_station = CuttingStation(OK_BUTTON, CANCEL_BUTTON, REPRINT_BUTTON, RESET_PIN, length, lock)
    encoder = get_encoder()
    gui = GUI(length)

    # Handle exit gracefully
    signal.signal(signal.SIGTERM, stop)

    log.info(get_ip_address('eth0'))
    log.info("Main: %s" % os.getpid())

    try:
        cut_station.start()
        gui.start()
        log.info("SDL pid: %s" % gui.pid)

        while running:
            try:
                line = encoder.readline()
            except (SerialException, AttributeError):
                if encoder:
                    encoder.close()
                encoder = get_encoder()
                line = 0

            if line:
                try:
                    cut_station.update_count(int(line))
                except ValueError:
                    pass
        cleanup()
    except KeyboardInterrupt:
        cleanup()
