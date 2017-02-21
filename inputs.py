from threading import Thread
import RPi.GPIO as GPIO
from os import system
from time import sleep


class Inputs(Thread):
    def __init__(self, buttons, sounds, gui_conn):
        Thread.__init__(self)
        self.buttons = buttons
        self.sounds = sounds
        self.counter = 0
        self.gui_conn = gui_conn

    def beep(self, channel):
        if channel in self.sounds:
            system('mpg123 -q %s &' % self.sounds[channel])

    def update_gui(self):
        # Update GUI
        feet, counter = divmod(self.counter, 600)
        inches = int(counter) / 50
        self.gui_conn.send("Feet: %s, Inches %s" % (feet, inches))

    def add_count(self, count):
        self.counter += count
        self.update_gui()

    def get_count(self):
        return self.counter

    def run(self):
        while True:
            for button, prev_state in self.buttons.items():
                pressed = GPIO.input(button)
                if pressed and prev_state is False:
                    self.counter = 0
                    self.update_gui()
                    self.buttons[button] = True
                    self.beep(button)
                    # print_test_label(button)
                elif not pressed and prev_state is True:
                    self.buttons[button] = False
            sleep(0.1)
