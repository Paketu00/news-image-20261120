"""The World in One Page - Friday, 20 November 2026.

A self-contained Python program (standard library only) that draws a
newspaper front page summing up the world's news of 20 November 2026
and writes it as a PNG file named entry.png.

The picture is drawn pixel by pixel into an in-memory canvas with a
small built-in bitmap typeface, then encoded as a PNG by hand.  The
program uses no network, no randomness and no clock, so two runs
always produce exactly the same bytes.

Output locations are tried in order and every attempt is guarded:
the directory named by the MAKEFUN_OUTPUT_DIR environment variable,
then /output, then the current working directory.  A location that
cannot be written is skipped quietly; the program never crashes
just because one path is read-only.
"""

import binascii
import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (246, 241, 229)
INK = (20, 19, 17)
SOFT = (74, 70, 62)
RED = (163, 32, 22)
NAVY = (18, 33, 66)
GOLD = (203, 154, 44)
PANEL = (233, 225, 206)
SKYLINE = (9, 16, 34)
WHITE = (248, 246, 238)

# A 5x7 pixel typeface.  Each glyph is seven rows of five bits,
# written as strings so the shapes stay easy to proof-read.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10001", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
}


class Canvas:
    """A plain RGB pixel buffer with tiny drawing primitives."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(bytes(colour) * (width * height))

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            at = (y * self.width + x) * 3
            self.pixels[at:at + 3] = bytes(colour)

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            at = (yy * self.width + x0) * 3
            self.pixels[at:at + len(row)] = row

    def frame_rect(self, x, y, w, h, colour, thick=1):
        self.fill_rect(x, y, w, thick, colour)
        self.fill_rect(x, y + h - thick, w, thick, colour)
        self.fill_rect(x, y, thick, h, colour)
        self.fill_rect(x + w - thick, y, thick, h, colour)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, thick, thick, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, radius, colour):
        r2 = radius * radius
        for yy in range(cy - radius, cy + radius + 1):
            for xx in range(cx - radius, cx + radius + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r2:
                    self.set_pixel(xx, yy, colour)

    def ring(self, cx, cy, radius, colour, thick=2):
        outer = radius * radius
        inner = (radius - thick) * (radius - thick)
        for yy in range(cy - radius, cy + radius + 1):
            for xx in range(cx - radius, cx + radius + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if inner <= d2 <= outer:
                    self.set_pixel(xx, yy, colour)


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, colour, bold=False):
    pen = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == "1":
                    cv.fill_rect(pen + col_i * scale, y + row_i * scale,
                                 scale, scale, colour)
                    if bold:
                        cv.fill_rect(pen + col_i * scale + 1,
                                     y + row_i * scale, scale, scale, colour)
        pen += 6 * scale
    return pen


def draw_centered(cv, y, text, scale, colour, bold=False):
    x = (cv.width - text_width(text, scale)) // 2
    draw_text(cv, x, y, text, scale, colour, bold)


def draw_right(cv, right_x, y, text, scale, colour, bold=False):
    draw_text(cv, right_x - text_width(text, scale), y, text, scale,
              colour, bold)


def wrap_text(text, max_chars):
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if len(trial) <= max_chars:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_strike_panel(cv, x, y, w, h):
    """Night sky over a city: falling streaks and three bursts."""
    cv.fill_rect(x, y, w, h, NAVY)
    ground = y + h - 12
    # Silhouette rooftops along the bottom edge.
    roofs = [(0, 10), (52, 16), (118, 8), (176, 14), (244, 9), (306, 15),
             (372, 8), (430, 13), (498, 9), (560, 16), (628, 8), (690, 12),
             (756, 9), (820, 15), (884, 10)]
    for off, tall in roofs:
        if x + off < x + w:
            cv.fill_rect(x + off, ground - tall, 44, tall, SKYLINE)
    cv.fill_rect(x, ground, w, 2, GOLD)
    # A few still stars.
    for sx, sy in [(30, 8), (150, 14), (330, 6), (520, 12), (700, 7),
                   (860, 15), (910, 5), (240, 18), (620, 20)]:
        cv.fill_rect(x + sx, y + sy, 2, 2, WHITE)
    # Descending streaks, each ending in a burst above the rooftops.
    streaks = [(96, 138, 30), (268, 306, 38), (452, 486, 26),
               (640, 676, 40), (806, 842, 30)]
    for sx, ex, drop in streaks:
        x0 = x + sx
        x1 = x + ex
        y0 = y + 4
        y1 = y + drop
        cv.line(x0, y0, x1, y1, WHITE, 2)
        for dx, dy in [(-9, 0), (9, 0), (0, -9), (0, 7), (-7, -7),
                       (7, -7), (-7, 6), (7, 6)]:
            cv.line(x1, y1, x1 + dx, y1 + dy, GOLD, 2)
        cv.disc(x1, y1, 3, RED)


def draw_market_chart(cv, x, y, w, h):
    """A small plunging line chart for the markets story."""
    cv.fill_rect(x, y, w, h, PANEL)
    cv.frame_rect(x, y, w, h, SOFT, 1)
    values = [8, 10, 9, 13, 12, 17, 21, 20, 26, 31, 30, 36]
    step = (w - 16) // (len(values) - 1)
    points = []
    for i, v in enumerate(values):
        px = x + 8 + i * step
        py = y + 4 + v * (h - 10) // 40
        points.append((px, py))
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        cv.line(ax, ay, bx, by, RED, 2)
    cv.disc(points[-1][0], points[-1][1], 3, RED)
    cv.fill_rect(x + 4, y + h - 17, text_width("-5.28%", 2) + 6, 15, PANEL)
    draw_text(cv, x + 7, y + h - 16, "-5.28%", 2, RED, bold=True)


def draw_mercury(cv, cx, cy):
    """A small cratered planet for the space story."""
    cv.disc(cx, cy, 17, (206, 178, 128))
    cv.ring(cx, cy, 17, INK, 1)
    for dx, dy, r in [(-6, -4, 3), (5, 2, 4), (-2, 8, 2), (8, -8, 2)]:
        cv.disc(cx + dx, cy + dy, r, (178, 148, 100))
    # A tiny craft approaching from the upper right.
    cv.fill_rect(cx + 24, cy - 26, 7, 7, INK)
    cv.line(cx + 21, cy - 19, cx + 12, cy - 10, INK, 1)
    cv.line(cx + 34, cy - 29, cx + 27, cy - 22, SOFT, 1)


class Column:
    """Stacks stories down one newspaper column, tracking the y cursor."""

    def __init__(self, cv, x, width):
        self.cv = cv
        self.x = x
        self.width = width
        self.y = 0

    def rule(self):
        self.cv.fill_rect(self.x, self.y, self.width, 1, SOFT)
        self.y += 12

    def kicker(self, text):
        draw_text(self.cv, self.x, self.y, text, 2, RED, bold=True)
        self.y += 20

    def headline(self, lines):
        for line in lines:
            draw_text(self.cv, self.x, self.y, line, 3, INK, bold=True)
            self.y += 25
        self.y += 3

    def body(self, text):
        max_chars = self.width // 12
        for line in wrap_text(text, max_chars):
            draw_text(self.cv, self.x, self.y, line, 2, INK)
            self.y += 18
        self.y += 6


def compose():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    margin = 40
    inner_w = WIDTH - 2 * margin

    # Page frame and masthead.
    cv.frame_rect(14, 14, WIDTH - 28, HEIGHT - 28, INK, 3)
    cv.frame_rect(21, 21, WIDTH - 42, HEIGHT - 42, INK, 1)
    draw_centered(cv, 32, "SHENZHEN - KYIV - THE HAGUE - BRUSSELS - "
                          "LONDON - NEW YORK - LIMA", 2, SOFT)
    draw_centered(cv, 54, "THE WORLD IN ONE PAGE", 7, INK, bold=True)
    cv.fill_rect(margin, 110, inner_w, 5, INK)
    cv.fill_rect(margin, 119, inner_w, 2, INK)
    draw_text(cv, margin, 129, "FRIDAY, 20 NOVEMBER 2026", 2, INK, bold=True)
    draw_centered(cv, 132, "SOURCES: REUTERS - AP - ISW - USGS - XINHUA",
                  1, SOFT)
    draw_right(cv, WIDTH - margin, 129, "ONE DAY, ONE IMAGE", 2, INK,
               bold=True)
    cv.fill_rect(margin, 150, inner_w, 1, SOFT)

    # Lead story: missiles in Poland hours after the Shenzhen talks.
    y = 162
    draw_text(cv, margin, y, "EUROPE - WAR IN UKRAINE", 2, RED, bold=True)
    y += 26
    for line in ("MISSILES LAND IN POLAND", "HOURS AFTER PEACE TALK"):
        draw_text(cv, margin, y, line, 6, INK, bold=True)
        y += 46
    y += 2
    lead = ("TWO RUSSIAN MISSILES AND A DRONE FELL ON POLISH SOIL DURING "
            "NOVEMBER'S BIGGEST STRIKE ON UKRAINE - 515 MISSILES AND "
            "DRONES IN ALL. NATO CALLED IT A GRAVE VIOLATION. TRUMP, IN "
            "SHENZHEN, CALLED HIS PUTIN TALKS VERY GOOD.")
    for line in wrap_text(lead, inner_w // 12):
        draw_text(cv, margin, y, line, 2, INK)
        y += 19
    y += 8
    draw_strike_panel(cv, margin, y, inner_w, 54)
    caption = "THE NIGHT SKY OVER UKRAINE, 19-20 NOVEMBER"
    draw_text(cv, WIDTH - margin - text_width(caption, 1) - 8, y + 45,
              caption, 1, WHITE)
    y += 66
    cv.fill_rect(margin, y, inner_w, 1, SOFT)
    y += 12

    # Left column: justice, markets, Europe.
    left = Column(cv, margin, 456)
    left.y = y
    left.kicker("THE HAGUE - JUSTICE")
    left.headline(["WORLD COURT: MYANMAR", "COMMITTED GENOCIDE"])
    left.body("THE FIRST TIME THE COURT HAS FOUND A STATE RESPONSIBLE "
              "FOR GENOCIDE. MYANMAR MUST MAKE REPARATIONS TO THE "
              "ROHINGYA - AND CALLED THE RULING UNFAIR.")
    left.rule()
    left.kicker("NEW YORK - MARKETS")
    left.headline(["AI SELL-OFF SINKS", "WALL STREET"])
    left.body("NASDAQ -5.28% ERASES ITS 2026 GAINS. S+P 500 -3.70%. "
              "NVIDIA -14% DESPITE STRONG EARNINGS. BITCOIN BELOW $60,000.")
    draw_market_chart(cv, left.x, left.y, 220, 40)
    left.y += 50
    left.rule()
    left.kicker("BRUSSELS - EUROPE")
    left.headline(["EU AND BRITAIN SEAL", "FOOD, CARBON, YOUTH"])
    left.body("FOOD TRADE EASED, CARBON MARKETS LINK FROM 2028, "
              "100,000 YOUNG PEOPLE A YEAR TO WORK OR STUDY ABROAD.")

    # Right column: Asia-Pacific, space, the Americas.
    right = Column(cv, 528, 456)
    right.y = y
    right.kicker("SHENZHEN - APEC SUMMIT")
    right.headline(["XI AND PRABOWO LAUNCH", "PARTNERSHIP TALKS"])
    right.body("CHINA AND INDONESIA OPEN TALKS ON A FULL ECONOMIC "
               "PARTNERSHIP. 35 BUSINESS DEALS WORTH $15 BILLION "
               "SIGNED AT APEC.")
    right.rule()
    right.kicker("SPACE - EUROPE AND JAPAN")
    head_y = right.y
    right.headline(["AFTER 8 YEARS, PROBE", "REACHES MERCURY"])
    draw_mercury(cv, right.x + right.width - 24, head_y + 22)
    right.body("BEPICOLOMBO ENDS AN EIGHT-YEAR, SIX-BILLION-MILE "
               "VOYAGE AND PREPARES TO ORBIT MERCURY, ONLY THE "
               "SECOND CRAFT EVER.")
    right.rule()
    right.kicker("THE AMERICAS")
    right.headline(["JURY CONVICTS MAN IN", "PALISADES FIRE CASE"])
    right.body("GUILTY OF STARTING THE DEADLY 2025 FIRE THAT KILLED "
               "12 AND DESTROYED THOUSANDS OF HOMES.")
    right.y += 2
    draw_text(cv, right.x, right.y, "PERU - 6.7 QUAKE SHAKES THE ANDES",
              2, INK, bold=True)
    right.y += 20
    right.body("THE DEEP QUAKE NEAR JUNIN WAS FELT IN LIMA. "
               "NO DEATHS REPORTED.")

    # Bottom briefs band.
    band_y = 946
    cv.fill_rect(margin, band_y, inner_w, 48, INK)
    briefs = ("IN BRIEF: TANKER ABLAZE NEAR HORMUZ - MOURNERS' BOAT "
              "CAPSIZES IN NIGERIA - BAYER $7.25BN ROUNDUP DEAL OKAYED "
              "- MIGRANT BOAT CAPSIZES OFF SENEGAL")
    by = band_y + 8
    for line in wrap_text(briefs, (inner_w - 28) // 12):
        draw_text(cv, margin + 14, by, line, 2, WHITE)
        by += 18
    return cv


def encode_png(cv):
    raw = bytearray()
    stride = cv.width * 3
    for yy in range(cv.height):
        raw.append(0)
        start = yy * stride
        raw.extend(cv.pixels[start:start + stride])
    idat = zlib.compress(bytes(raw), 9)

    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload +
                struct.pack(">I", binascii.crc32(kind + payload)
                            & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.width, cv.height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def candidate_paths():
    paths = []
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if out_dir:
        paths.append(os.path.join(out_dir, "entry.png"))
    paths.append(os.path.join("/output", "entry.png"))
    paths.append(os.path.join(os.getcwd(), "entry.png"))
    seen = []
    for path in paths:
        if path not in seen:
            seen.append(path)
    return seen


def main():
    data = encode_png(compose())
    for path in candidate_paths():
        try:
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(path, "wb") as handle:
                handle.write(data)
            print("wrote", path, len(data), "bytes")
            return
        except OSError:
            continue
    print("no writable output location found")


if __name__ == "__main__":
    main()
