import os
import yaml

yaml_file = "../conf/conf.yaml"


class ParseYaml:
    """
    解析yaml配置文件
    """

    def __init__(self):
        yaml_file_abspath = os.path.join(os.path.dirname(__file__), yaml_file)
        self.yaml_file = yaml_file_abspath

    def parse_yaml(self):
        conf_list = []
        with open(self.yaml_file, encoding="utf-8") as conf_file:
            conf = yaml.safe_load_all(conf_file)
            for i in conf:
                conf_list.append(i)
        return conf_list

    def get_conf(self, key):
        conf_list = self.parse_yaml()
        ret = {}
        for conf in conf_list:
            if key in conf.keys():
                ret = conf[key]
        if len(ret) == 0:
            print("No such config in {}".format(self.yaml_file))
            return
        return ret


_conf_system = ParseYaml()
_conf = _conf_system.get_conf("testSystem")


def compose_url(addr, proto=_conf["proto"], host=_conf["host"], port=_conf["port"]):
    return proto + "://" + host + ":" + port + addr
