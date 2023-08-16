"""
Most of the code builds on this git,
where the "ANSI escape code" are listed
https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797

(https://en.wikipedia.org/wiki/ANSI_escape_code)
"""

import os

CLS_LINE = '\033[K'
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
ITALIC = '\033[3m'
UNDERLINE = '\033[4m'
STRIKETHROUGH = '\033[9m'

MOVE_UP_N = lambda n: f'\033[{n}A'
MOVE_DOWN_N = lambda n: f'\033[{n}B'
MOVE_RIGHT_N = lambda n: f'\033[{n}C'
MOVE_LEFT_N = lambda n: f'\033[{n}D'
SET_POS = lambda x,y: f'\033[{y};{x}H'

FG_RGB = lambda r,g,b: f'\033[38;2;{r};{g},{b}m'
BG_RGB = lambda r,g,b: f'\033[48;2;{r};{g};{b}m'
COLOR_FG = lambda id: f'\033[38;5;{id}m'
COLOR_BG = lambda id: f'\033[48;5;{id}m'

BLACK = COLOR_FG(0)
RED = COLOR_FG(1)
GREEN = COLOR_FG(2)
YELLOW = COLOR_FG(3)
BLUE = COLOR_FG(4)
PINK = COLOR_FG(5)
CYAN = COLOR_FG(6)

def set_cur_pos(x,y):
    print(f'\033[{x};{y}H', end='')

def cls() -> None:
    os.system('cls')

def win_size() -> tuple[int, int]:
    return os.get_terminal_size()

def save_cur_pos() -> None:
    print('\033[s', end='')

def reset_cur_pos() -> None:
    print('\033[u', end='')

def cls_line():
    print(CLS_LINE, end='')

def get_rgb_fg(r,g,b):
    return f'\033[38;2;{r};{g},{b}m'

def get_rgb_bg(r,g,b):
    return f'\033[48;2;{r};{g};{b}m'

def set_cur_invis():
    print('\033[?25l', end='')

def set_cur_visible():
    print('\033[?25h', end='')

def save_screen():
    print('\033[?47h', end='')

def restore_screen():
    print('\033[?47l', end='')