from enum import Enum


class PDFPageSizeInch(Enum):
    """
    Standard PDF page sizes in inches (calculated from 300 DPI).

    Members:
        A0, A1, A2, A3, A4, A5, A6: ISO 216 standard paper sizes.
        LETTER: US Letter size.
        LEGAL: US Legal size.
        TABLOID: US Tabloid size.
        LEDGER: US Ledger size (landscape orientation).
        SQUARE_10, SQUARE_12: Square formats in inches.
        ART_PRINT_50x70, ART_PRINT_60x80, ART_PRINT_70x100: Common art print sizes in inches.

    Each member is a dictionary with keys:
        width: page width in inches
        height: page height in inches
    """

    A0 = {"width": 33.11, "height": 46.81}
    A1 = {"width": 23.39, "height": 33.11}
    A2 = {"width": 16.54, "height": 23.39}
    A3 = {"width": 11.69, "height": 16.54}
    A4 = {"width": 8.27, "height": 11.69}
    A5 = {"width": 5.83, "height": 8.27}
    A6 = {"width": 4.13, "height": 5.83}

    LETTER = {"width": 8.50, "height": 11.00}
    LEGAL = {"width": 8.50, "height": 14.00}
    TABLOID = {"width": 11.00, "height": 17.00}

    LEDGER = {"width": 17.00, "height": 11.00}

    SQUARE_10 = {"width": 10.00, "height": 10.00}
    SQUARE_12 = {"width": 12.00, "height": 12.00}

    ART_PRINT_50x70 = {"width": 19.69, "height": 27.56}
    ART_PRINT_60x80 = {"width": 23.62, "height": 31.50}
    ART_PRINT_70x100 = {"width": 27.56, "height": 39.37}
