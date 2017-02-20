import RPi.GPIO as GPIO


class RotaryEncoder:
    def __init__(self, a_pin, b_pin):
        # Pins
        self.a_pin = a_pin
        self.b_pin = b_pin

        self.counter = 0

    def a_falling(self, channel):
        if GPIO.input(self.b_pin):
            self.counter -= 1

    def b_falling(self, channel):
        if GPIO.input(self.a_pin):
            self.counter += 1

    def run(self):
        GPIO.add_event_callback(self.a_pin, self.a_falling)
        GPIO.add_event_callback(self.b_pin, self.b_falling)
