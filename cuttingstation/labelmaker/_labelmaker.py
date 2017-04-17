from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from subprocess import call
from os import devnull
from . import LabelTypes


class LabelMaker:
    def __init__(self):
        # Label location
        self._lbl_path = '/tmp/label.pdf'

        # Uline 3in x 1in direct thermal label
        self.lblSize = (216, 72)

        # Register fonts
        fonts = ['OpenSans-Bold', 'OpenSans-Regular']
        for font in fonts:
            f = TTFont(font, 'fonts/' + font + '.ttf')
            registerFont(f)

        # Label vars
        self.cut_counter = 0
        self._left = 4
        self._top = 56
        self._middle = 32
        self._bottom = 6
        self.regular = 'OpenSans-Regular'
        self.bold = 'OpenSans-Bold'

    def _create_cut_label(self, feet):
        c = self._new_lbl(feet)

        # Draw part number
        c.setFont(self.regular, 12)
        c.drawString(self._left, self._bottom, '935122%sR' % feet)

        # Finalize page and save file
        c.showPage()
        c.save()

    def _create_cancel_label(self, feet, inches):
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

    def print_label(self, feet, inches, label_type):
        if label_type == LabelTypes.cut:
            self._create_cut_label(feet)
        elif label_type == LabelTypes.cancel:
            self._create_cancel_label(feet, inches)

        call(['/usr/bin/lp', self._lbl_path],
             stdout=open(devnull, 'w'),
             close_fds=True)

    def reprint_label(self):
        call(['/usr/bin/lp', self._lbl_path],
             stdout=open(devnull, 'w'),
             close_fds=True)

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
