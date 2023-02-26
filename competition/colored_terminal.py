# print colored in terminal
class C:
    # type
    HEADER = "\033[95m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # color
    Black = "\033[30m"
    Red	= "\033[31m"
    Green = "\033[32m"
    Yellow = "\033[33m"
    Blue = "\033[34m"
    Magenta = "\033[35m"
    Cyan = "\033[36m"
    White = "\033[37m"

    # bright color
    black = "\033[90m"
    red = "\033[91m"
    green = "\033[92m"
    yellow = "\033[93m"
    blue = "\033[94m"
    magenta = "\033[95m"
    cyan = "\033[96m"
    white = "\033[97m"

    # background_color
    B_Black = "\033[40m"
    B_Red = "\033[41m"
    B_Green = "\033[42m"
    B_Yellow = "\033[43m"
    B_Blue = "\033[44m"
    B_Magenta = "\033[45m"
    B_Cyan = "\033[46m"
    B_White = "\033[47m"

    # bright background_color
    B_black = "\033[100m"
    B_red = "\033[101m"
    B_green = "\033[102m"
    B_yellow = "\033[103m"
    B_blue = "\033[104m"
    B_magenta = "\033[105m"
    B_cyan = "\033[106m"
    B_white = "\033[107m"

    # RGB color \033[38;2;r;g;bm
    # RGB background \033[48;2;r;g;bm

    # reset
    End = "\033[0m"