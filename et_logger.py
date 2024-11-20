from contextlib import contextmanager
import sys
import datetime

class LogLevel:
    TRACE=0
    DEBUG=1
    INFO=2

class Colors:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[32m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DEFAULT = '\033[0m'

@contextmanager
def colorize(color, bold=False):
    sys.stdout.write(color)
    if bold: sys.stdout.write(Colors.BOLD)
    sys.stdout.flush()
    yield
    sys.stdout.write(Colors.DEFAULT)
    sys.stdout.flush()

@contextmanager
def indent(logger):
    logger.indent_increase()
    yield
    logger.indent_decrease()

class Logger:
    def __init__(self, level=LogLevel.INFO, indent_step=2):
        if level < LogLevel.TRACE or level > LogLevel.INFO:
            raise Exception(f"Invalid LogLevel passed to Logger: {level}")
        self.LOG_LEVEL=level
        self.history = []
        self.indent_step=indent_step
        self.indent=0
        self.ignore_indent=False

    def indent_increase(self):
        self.indent += self.indent_step

    def indent_decrease(self):
        if self.indent == 0: return
        self.indent -= self.indent_step

    def log(self, log_level, message, bold, color, **kwargs):
        if log_level < self.LOG_LEVEL: return
        indent_char = "" if self.ignore_indent else " "
        msg = indent_char * self.indent + message
        with colorize(color, bold):
            print(msg, **kwargs)

        if "end" in kwargs.keys():
            self.history.append(msg + kwargs["end"])
            self.ignore_indent=True
        else:
            self.history.append(msg + "\n")
            self.ignore_indent=False

    def trace(self, message, bold=False, color=Colors.DEFAULT):
        self.log(LogLevel.TRACE, message, bold, color)

    def trace_n(self, message, bold=False, color=Colors.DEFAULT):
        self.log(LogLevel.TRACE, message, bold, color, end=" ")

    def debug(self, message, bold=False, color=Colors.DEFAULT):
        self.log(LogLevel.DEBUG, message, bold, color)

    def debug_n(self, message, bold=False, color=Colors.DEFAULT):
        self.log(LogLevel.DEBUG, message, bold, color, end=" ")

    def info(self, message, bold=False, color=Colors.DEFAULT):
        self.log(LogLevel.INFO, message, bold, color)

    def info_n(self, message, bold=False, color=Colors.DEFAULT):
        self.log(LogLevel.INFO, message, bold, color, end=" ")

    def clear_history(self):
        self.history = []

    def dump(self, file_name=None, use_date_suffix=False):
        parts = []
        if file_name is not None:
            parts.append(file_name)
        if use_date_suffix:
            parts.append(str(datetime.datetime.now()).replace(' ', '_'))
        if len(parts) == 0: parts.append("output")
        parts.append("log")
        complete_file_name = ".".join(parts)
        with open(complete_file_name, "w") as outfile:
            outfile.writelines(self.history)
        return complete_file_name
