import os
import yaml
import json

from common.log import logger
from common.error import MyError

yaml_file = "../conf/conf.yaml"
logger = logger()


class ParseYaml:
    """
    解析yaml配置文件
    """

    def __init__(self):
        yaml_file_abspath = os.path.join(os.path.dirname(__file__), yaml_file)
        self.yaml_file = os.path.abspath(yaml_file_abspath)
        logger.info("Using config file: {}".format(self.yaml_file))

    def parse_yaml(self):
        conf_list = []
        with open(self.yaml_file, encoding="utf-8") as conf_file:
            conf = yaml.safe_load_all(conf_file)
            for i in conf:
                conf_list.append(i)
        logger.info(json.dumps(conf_list))
        return conf_list

    def get_conf(self, key):
        conf_list = self.parse_yaml()
        ret = {}
        for conf in conf_list:
            if key in conf.keys():
                ret = conf[key]
                logger.info("Return config {} from {}:\nType: {}\nContent: {}".format(key, self.yaml_file, type(ret),
                                                                                      json.dumps(ret)))
                break
        if len(ret) == 0:
            message = "Config {} is empty or not defined in {}.".format(key, self.yaml_file)
            raise MyError(message)
        return ret


_conf_system = ParseYaml()
_conf = _conf_system.get_conf("testSystem")


def compose_url(addr, proto=_conf["proto"], host=_conf["host"], port=_conf["port"]):
    return proto + "://" + host + ":" + port + addr
