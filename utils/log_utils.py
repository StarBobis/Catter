'''
How to log colored text on terminal:

BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'
RESET = '\033[0m'

BOLD = '\033[1m'
UNDERLINE = '\033[4m'
BACKGROUND_YELLOW = '\033[43m'

print(BACKGROUND_YELLOW + BLACK + BOLD + "Warning: This is a warningg message" + RESET)
'''

# Nico: notice, all print() and output should call these method, so we can make them log to file easily when switch to GUI.

class LOG:
    @classmethod
    def info(cls,input):
        if type(input) == list:
            for something in input:
                print(something)
        
        else:
            print(input)


    @classmethod
    def warning(cls,input:str):
        print("\033[33m" + "Warning: " + input + "\033[0m")
        cls.newline()

    @classmethod
    def newline(cls):
        print("\033[32m" +"------------------------------------------------------------------------------------------------------------------------------" + "\033[0m")

    