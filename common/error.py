from common.log import logger


logger = logger("MyError")


class MyError(Exception):
    def __init__(self, message):
        self.message = message
        logger.error(self.message)

    def __str__(self):
        return repr(self.message)


class ConfKeyError(MyError):
    def __init__(self, message):
        MyError.__init__(message)


class FormatError(MyError):
    def __init__(self, message):
        MyError.__init__(message)


class MethodError(MyError):
    def __init__(self, message):
        MyError.__init__(message)


class CompareResultError(MyError):
    def __init__(self, message):
        MyError.__init__(message)
