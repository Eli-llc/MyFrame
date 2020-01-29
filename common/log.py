import logging
import os


class _MyLog:
    """
    自定义log等级，来控制log的输出
    """

    def __init__(self, name=None):
        self.name = name

    @staticmethod
    def _formatter(level=None):
        if level == "all":
            datefmt = "%Y-%m-%d %H:%M:%S %a"
            formatter = "%(asctime)s %(name)s %(levelname)s %(pathname)s %(funcName)s %(message)s"
        else:
            datefmt = "%Y-%m-%d %H:%M:%S"
            formatter = "%(asctime)s %(levelname)s %(message)s"
        return logging.Formatter(fmt=formatter, datefmt=datefmt)

    @staticmethod
    def _log_name(filename):
        log_path = os.path.join(os.path.dirname(__file__), "../logs")
        log_name = os.path.join(log_path, filename)
        return os.path.abspath(log_name)

    def _file_handler(self, filename, level=None):
        handler = logging.FileHandler(filename)
        formatter = self._formatter(level)
        handler.setFormatter(formatter)
        return handler

    def _stream_handler(self, level=None):
        handler = logging.StreamHandler()
        formatter = self._formatter(level)
        handler.setFormatter(formatter)
        return handler

    def _get_logger(self):
        """
        - 主要是添加handler
        这里添加了三个handler，把log输出到不同的位置
        : 第一个是输出到error.log，log不是很详细
        : 第二个是输出到debug.log，是最详细的log
        : 第三个是输出到终端，方便看到简略信息
        :return: 创建好的Logger。这个Logger同logging模块返回的类似，只是添加了上述handler
        """
        my_logger = logging.getLogger(self.name)
        # my_logger需要接受任何等级的log，否则下面debug.log不会接收到低等级的log
        my_logger.setLevel(10)
        # 判断logger是否已有handler，防止日志的重复打印
        if not my_logger.handlers:
            error_log = self._file_handler(self._log_name("error.log"))
            error_log.setLevel(40)  # error.log只存储error以上的log
            debug_log = self._file_handler(self._log_name("debug.log"), level="all")
            # 这里终端的输出和error.log存储的内容是一样的
            stdout = self._stream_handler("all")
            my_logger.addHandler(error_log)
            my_logger.addHandler(debug_log)
            my_logger.addHandler(stdout)
        return my_logger


def logger(name="MyLogger"):
    return _MyLog(name)._get_logger()
