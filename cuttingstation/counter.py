from threading import Thread
import RPi.GPIO as GPIO
from os import system, devnull
from time import sleep
from subprocess import call
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont


class Counter(Thread):
    def __init__(self, ok_button, cancel_button, reprint_button, length, lock):
        Thread.__init__(self)
        self.running = False

        # Uline 3in x 1in direct thermal label
        self.lblSize = (216, 72)

        # Register fonts
        fonts = ['OpenSans-Bold', 'OpenSans-Regular']
        for font in fonts:
            f = TTFont(font, 'fonts/' + font + '.ttf')
            registerFont(f)

        # Label location
        self._lbl_path = '/tmp/label.pdf'

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

        # Label vars
        self.cut_counter = 0
        self._left = 4
        self._top = 56
        self._middle = 32
        self._bottom = 6
        self.regular = 'OpenSans-Regular'
        self.bold = 'OpenSans-Bold'

    def beep(self, channel):
        if channel in self.sounds:
            system('mpg123 -q %s &' % self.sounds[channel])

    def get_length(self):
        feet, counter = divmod(self.counter, 600)
        inches = int(counter) / 50
        return feet, inches

    def update_gui(self):
        feet, inches = self.get_length()
        # Update GUI
        self.lock.acquire()
        self.length.value = "Feet: %s, Inches %s" % (feet, inches)
        self.lock.release()

    def add_count(self, count):
        self.counter += count
        self.update_gui()

    def _new_lbl(self, feet):
        self.cut_counter += 1
        c = canvas.Canvas(self._lbl_path, pagesize=self.lblSize)

        # Draw Footage
        c.setFont(self.bold, 16)
        c.drawString(self._left, self._top, "%s'" % feet)

        # Draw description
        c.setFont(self.regular, 12)
        c.drawString(self._left, self._middle, '12/2 ROMEX')

        # Draw serial number
        width = self.lblSize[0]
        lc_width = c.stringWidth('L1C%s' % self.cut_counter, self.regular, 12)
        c.drawString(width - lc_width - 6, self._middle, 'L1C%s' % self.cut_counter)

        return c

    def create_cut_label(self):
        feet, inches = self.get_length()
        c = self._new_lbl(feet)

        # Draw part number
        c.setFont(self.regular, 12)
        c.drawString(self._left, self._bottom, '935122%sR' % feet)

        # Finalize page and save file
        c.showPage()
        c.save()

    def create_cancel_label(self):
        feet, inches = self.get_length()
        c = self._new_lbl(feet)

        # Draw inches
        ft_size = c.stringWidth("%s'" % feet, self.bold, 16)
        c.setFont(self.bold, 16)
        c.drawString(ft_size, self._top, '  %s"' % inches)

        # Draw description
        c.setFont(self.regular, 12)
        c.drawString(self._left, self._bottom, "Canceled cut")

        # Finalize and save
        c.showPage()
        c.save()

    def print_label(self, lbl):
        lbl()
        call(['/usr/bin/lp', self._lbl_path],
             stdout=open(devnull, 'w'),
             close_fds=True)

    def reprint_label(self):
        call(['/usr/bin/lp', self._lbl_path],
             stdout=open(devnull, 'w'),
             close_fds=True)

    def terminate(self):
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            for button, prev_state in self.buttons.items():
                pressed = GPIO.input(button)
                if pressed and prev_state is False:
                    if button == self.ok_button:
                        self.print_label(self.create_cut_label)

                    if button == self.cancel_button:
                        self.print_label(self.create_cancel_label)

                    if button == self.reprint_button:
                        self.reprint_label()

                    self.counter = 0
                    self.update_gui()
                    self.buttons[button] = True
                    self.beep(button)
                elif not pressed and prev_state is True:
                    self.buttons[button] = False
            sleep(0.1)
