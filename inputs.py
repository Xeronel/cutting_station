from threading import Thread
import RPi.GPIO as GPIO
from os import system, devnull
from time import sleep
from subprocess import call
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont


class Inputs(Thread):
    def __init__(self, ok_button, cancel_button, reprint_button, length, lock):
        Thread.__init__(self)

        # Uline 3in x 1in direct thermal label
        self.lblSize = (216, 72)

        # Register fonts
        fonts = ['OpenSans-Bold', 'OpenSans-Regular']
        for font in fonts:
            f = TTFont(font, 'fonts/' + font + '.ttf')
            registerFont(f)

        # Label location
        self.label = '/tmp/label.pdf'

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
        self.counter = 0
        self.length = length
        self.lock = lock
        self.cut_counter = 0

    def beep(self, channel):
        if channel in self.sounds:
            system('mpg123 -q %s &' % self.sounds[channel])

    def update_gui(self):
        # Update GUI
        feet, counter = divmod(self.counter, 600)
        inches = int(counter) / 50
        self.lock.acquire()
        self.length.value = "Feet: %s, Inches %s" % (feet, inches)
        self.lock.release()

    def add_count(self, count):
        self.counter += count
        self.update_gui()

    def create_label(self):
        self.cut_counter += 1
        c = canvas.Canvas(self.label, pagesize=self.lblSize)
        width = self.lblSize[0]
        x_offset = 4

        # Draw Footage
        c.setFont('OpenSans-Bold', 16)
        c.drawString(x_offset, 56, "30'")

        # Draw description and part number
        c.setFont('OpenSans-Regular', 12)
        c.drawString(x_offset, 32, '12/2 ROMEX')
        c.drawString(x_offset, 6, '93512230R')

        # Draw serial number
        lc_width = c.stringWidth('L1C%s' % self.cut_counter, 'OpenSans-Regular', 12)
        c.drawString(width - lc_width - 6, 32, 'L1C%s' % self.cut_counter)

        # Finalize page and save file
        c.showPage()
        c.save()

    def print_label(self):
        self.create_label()
        call(['/usr/bin/lp', self.label],
             stdout=open(devnull, 'w'),
             close_fds=True)

    def reprint_label(self):
        call(['/usr/bin/lp', self.label],
             stdout=open(devnull, 'w'),
             close_fds=True)

    def run(self):
        while True:
            for button, prev_state in self.buttons.items():
                pressed = GPIO.input(button)
                if pressed and prev_state is False:
                    self.counter = 0
                    self.update_gui()
                    self.buttons[button] = True
                    self.beep(button)

                    if button == self.ok_button:
                        self.print_label()

                    if button == self.reprint_button:
                        self.reprint_label()
                elif not pressed and prev_state is True:
                    self.buttons[button] = False
            sleep(0.1)
