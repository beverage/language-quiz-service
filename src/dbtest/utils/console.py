from enum import StrEnum

class Color(StrEnum):
    BRIGHT_BLUE  = '\033[94m'
    STRONG_GREEN = '\033[38;5;46m'
    STRONG_RED   = '\033[38;5;196m'
    WHITE        = '\033[37m'

class Style(StrEnum):
    BOLD  = '\033[1m'
    RESET = '\033[0m'

class Answers(StrEnum):
    CORRECT   = Style.BOLD + Color.WHITE + "[" + Color.STRONG_GREEN + "X" + Color.WHITE + "]" + Style.RESET
    INCORRECT = Style.BOLD + Color.WHITE + "[" + Color.STRONG_RED   + "-" + Color.WHITE + "]" + Style.RESET

