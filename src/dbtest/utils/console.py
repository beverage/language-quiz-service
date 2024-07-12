from enum import StrEnum

class Style(StrEnum):
    BOLD  = '\033[1m'
    RESET = '\033[0m'

class Color(StrEnum):
    BOLD_WHITE   = f"\033[37m{Style.BOLD}"
    BRIGHT_BLUE  = '\033[94m'
    LIGHT_GRAY   = '\033[90m'
    STRONG_GREEN = '\033[38;5;46m'
    STRONG_RED   = '\033[38;5;196m'
    WHITE        = '\033[37m'

class Answers(StrEnum):
    CORRECT   = f"{Color.BOLD_WHITE}[{Color.STRONG_GREEN}X{Color.WHITE}]{Style.RESET}"
    INCORRECT = f"{Color.BOLD_WHITE}[{Color.STRONG_RED}-{Color.WHITE}]{Style.RESET}"
