from threading import Thread
import RPi.GPIO as GPIO
from os import system
from time import sleep
from labelmaker import LabelTypes, LabelMaker


class CuttingStation(Thread):
    def __init__(self, ok_button, cancel_button, reprint_button, reset_pin, length, lock):
        Thread.__init__(self)
        self.running = False
        self.reset_pin = reset_pin
        self.label_maker = LabelMaker()

        # Keep track of buttons last state
        # button, prev_state
        self.buttons = {
            ok_button: False,
            cancel_button: False,
            reprint_button: False
        }

        # Channel sound maps
        self.sounds = {
            ok_button: "sound/success.mp3",
            cancel_button: "sound/error.mp3",
            reprint_button: "sound/boop.mp3"
        }

        self.ok_button = ok_button
        self.cancel_button = cancel_button
        self.reprint_button = reprint_button
        self.inches = 0
        self.length = length
        self.lock = lock

    def beep(self, channel):
        if channel in self.sounds:
            system('mpg123 -q %s &' % self.sounds[channel])

    def get_length(self):
        feet, inches = divmod(self.inches, 12)
        return feet, inches

    def update_gui(self):
        feet, inches = self.get_length()
        # Update GUI
        self.lock.acquire()
        self.length.value = "Feet: %s, Inches: %s" % (feet, inches)
        self.lock.release()

    def update_count(self, inch):
        self.inches += inch
        if self.inches < 0:
            self.inches = 0
        self.update_gui()

    def reset_counter(self):
        GPIO.output(self.reset_pin, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(self.reset_pin, GPIO.LOW)

    def terminate(self):
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            for button, prev_state in self.buttons.items():
                pressed = not GPIO.input(button)
                if pressed and prev_state is False:
                    if button == self.ok_button:
                        self.label_maker.print_label(LabelTypes.cut, *self.get_length())

                    if button == self.cancel_button:
                        self.label_maker.print_label(LabelTypes.cancel, *self.get_length())

                    if button == self.reprint_button:
                        self.label_maker.reprint_label()

                    self.inches = 0
                    self.update_gui()
                    self.buttons[button] = True
                    self.beep(button)
                    self.reset_counter()
                    # Debounce time
                    sleep(0.1)
                elif not pressed and prev_state is True:
                    self.buttons[button] = False
            sleep(0.1)
