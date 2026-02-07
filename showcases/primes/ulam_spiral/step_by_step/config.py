from svan2d.core.color import Color

# Font path - adjust for your system
# macOS: /System/Library/Fonts/Supplemental/Arial.ttf
# Linux: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
# Windows: C:/Windows/Fonts/arial.ttf
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"

COLOR_ONE = Color(70, 70, 180)
COLOR_BACKGROUND = Color(10, 10, 30)
COLOR_PRIME = Color(255, 170, 0)
COLOR_COMPOSITE = Color(0, 0, 70)
COLOR_TEXT = Color(255, 255, 255)

NUM_RINGS = 42
RINGS_WITH_NUMBERS = 5
SQUARE_SIZE = 80
GAP = 40
SCENE_SIZE = 1200

FRAME_RATE = 60
TOTAL_FRAMES = 60 * NUM_RINGS
