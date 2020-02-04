import requests
import json
from jsonpath_rw import jsonpath, parse
import re
import sys
from time import sleep

from MySQLCon.mysqlcon import MySql
from common.login import cookie
from common.parseyaml import compose_url
from common.log import logger
from common.error import FormatError, MethodError

"""
执行测试用例
"""
logger = logger()
COOKIE = cookie


class TestCase:
    def __init__(self):
        self.mysql = MySql()

    def run(self):
        cases_enabled = self.mysql.get_case_ids()
        for case_id in cases_enabled:
            self.execute_and_result(case_id)

    def execute_and_result(self, case_id):
        response, data = self.run_case(case_id)
        result = self.get_result(response, data)
        print("{}\n{}\n{}".format("-" * 20, response.text, "-" * 20))
        self.mysql.update_mysql(case_id, result)

    def run_case(self, case_id):
        logger.info("Get case id: {}".format(case_id))
        data = self.mysql.get_data_by_id(case_id)
        if data.dependency_id and data.dependency_id.strip():
            data = self.handle_dependency(data)
        # print("data.delay is :", type(data.delay), data.delay) # data.delay is : <class 'int'> 0
        sleep(int(data.delay))
        url = compose_url(data.url)
        method = data.method
        headers = json.loads(data.header)
        headers.update(COOKIE)
        payload = data.request_data
        files = data.file or None
        if files:
            # 这里使用了exec函数，必须按照下面的方式，才能将数据库中files中的open函数执行。否则会出现如下ValueError
            # ValueError: cannot encode objects that are not 2-tuples
            # 下面s是exec执行的python语句。d是exec的一个命名空间，exec执行的结果将存放在这个字典中，
            # 然后在外面使用这个字典，才可以取出files的值
            s = "files = {}".format(files)
            d = {}
            exec(s, d)
            files = d["files"]
        logger.info("Now execute case: {}".format(case_id))
        if method == "post":
            response = requests.post(url=url, data=payload, headers=headers, files=files)
        elif method == "get":
            response = requests.get(url=url, data=payload, headers=headers, files=files)
        elif method == "delete":
            response = requests.delete(url=url, data=payload, headers=headers)
        else:
            raise MethodError("Method: {} not support!".format(method))
        return response, data

    def handle_dependency(self, data):
        """
        dependency_id   dependency_fragment                                 use_fragment                 other_str
        (1, 2, 3)       (((entity.situation[*], min),(1.2)),(2.1),(3.1))    (first, second, third)       use first str
        # 1. 循环执行依赖的case
        # 2. 将依赖的case执行的结果根据dependency_fragment进行处理，包括其中函数的执行
        # 3. 替换data中，数据中包含的需要被替换的变量
        :param data:
        :return:
        """
        # 简单判断输入参数格式的正确性
        dependency_id = json.loads(data.dependency_id)
        if not data.dependency_fragment:
            dependency_fragment = []
            logger.warning("dependency_fragment of {} is Null".format(data.id))
        else:
            dependency_fragment = json.loads(data.dependency_fragment)
        if not data.use_fragment:
            use_fragment = []
            logger.warning("use_fragment of {} is Null".format(data.id))
        else:
            use_fragment = json.loads(data.use_fragment)
        # 取出三个量的长度，如果不一致，说明输入数据不正确
        lens = set(map(len, (dependency_id, dependency_fragment, use_fragment)))
        # 因为dependency_fragment和use_fragment可能不会引用依赖的case_id，所以这里可能为空，所以减去{0}
        if not len(lens - {0}) == 1:
            raise FormatError(
                "The length of 'dependency_id, dependency_fragment, use_fragment' of case_id: {} is not "
                "equal!\nFilled blank with None if you need not reference dependency response.".format(
                    data.id))
        # 1. 循环执行依赖的case
        # 2. 将依赖的case执行的结果根据dependency_fragment进行处理，包括其中函数的执行
        match_list = []
        for i in range(len(dependency_id)):
            logger.info("Execute dependency case: {}".format(dependency_id[i]))
            response = self.run_case(dependency_id[i])
            response = response[0]
            if len(dependency_fragment) == len(dependency_id):
                match = self.match_result(dependency_fragment[i], response)
                match_list.append(match)
        # 3. 替换data中，数据中包含的需要被替换的变量
        if len(use_fragment) == len(dependency_id):
            logger.info("Before change data:\n{}".format(str(data)))
            data = self.change_data(data, use_fragment, match_list)
            logger.info("After change data:\n{}".format(str(data)))
        return data

    def get_result(self, response, data):
        # 拿到期望结果
        try:
            expect_json = json.loads(data.expect_result)
            response_json = response.json()
        except json.decoder.JSONDecodeError:
            if data.expect_result in response.text:
                return {"result": "pass"}
            else:
                return {"result": "fail", "actual_result": response.text}
        else:
            flag = True

            # 这个方法判断expect中的键值是否在actual中
            def extractor(expect, actual):
                nonlocal flag
                if isinstance(expect, dict):
                    # 如果expect是字典，那么就根据键来比对值是否相等，如果值是字典，则继续迭代
                    for expect_key in expect:
                        if expect_key in actual.keys():
                            flag = extractor(expect[expect_key], actual[expect_key])
                            if not flag:
                                return flag
                        else:
                            flag = False
                elif isinstance(expect, list):
                    # 如果expect是列表，则循环判断列表中的每个元素是否相等。如果元素是可迭代的，则继续迭代
                    for ele_expect in expect:
                        for ele_actual in actual:
                            if extractor(ele_expect, ele_actual):
                                flag = True
                                break
                            else:
                                flag = False
                else:
                    # 如果是普通的值，则直接判断是否相等，如果相等，则判断匹配成功
                    if not expect == actual:
                        flag = False
                    else:
                        flag = True
                return flag

            try:
                flag = extractor(expect_json, response_json)
            except Exception:
                flag = False
            if flag:
                return {"result": "pass"}
            else:
                return {"result": "fail", "actual_result": response.text}

    @staticmethod
    def match_result(fragment, response):
        """
        (
         fragment   (
                (entity.situation[*], min),
                (1.2)
            ),
            (2.1),
            (3.1)
        )
        :param fragment:
        :param response:
        :return:
        """
        result = []
        if not fragment:
            return [result]
        for frag in fragment:
            logger.info("In match_result: Frag is {}, type is {}".format(frag, type(frag)))  # frag: (entity.situation[*], min)
            pattern = parse(frag[0])
            logger.info("response.json is {}, type is {}".format(response.json(), type(response.json())))
            match_list = [match.value for match in pattern.find(response.json())]
            logger.info("match_list is {}".format(match_list))
            try:
                d = {}
                string = "result = {}({})".format(frag[1], match_list)
                exec(string, d)
                result.append(str(d["result"]))
            except IndexError:
                logger.warn("Dependency_fragment: {} not specify function name for match pattern.".format(frag))
            else:
                result.append(str(match_list).strip("[|]|(|)|{|}"))
        return [result]

    @staticmethod
    def change_data(data, use_fragment, match_list):
        """
        use_fragment: [[["situationID", "Case_name"], ["Name"]], ["EventId"]]
        :param data:
        :param use_fragment:
        :param match_list:
        :return:
        """
        data_return = list(data)
        # 从3开始是因为数据库中前3列都是不需要替换的，后面-5也是这个原因
        for index in range(3, len(data_return)-5):
            # 拿到每个case的use_fragment
            for fragment_case, match_case in zip(use_fragment, match_list):
                # 拿到当前case的多个匹配字段
                for frag_ele, match_ele in zip(fragment_case, match_case):
                    # 拿到当前匹配字段
                    for frag_sect, match_sect in zip(frag_ele, match_ele):
                        # 执行替换
                        pattern = re.compile(r"\$" + frag_sect)
                        try:
                            data_return[index] = pattern.sub(match_sect, data_return[index])
                        except TypeError:
                            pass
        fileds = (
            "id",
            "section",
            "case_name",
            "url",
            "method",
            "header",
            "request_data",
            "file", "delay",
            "dependency_id",
            "dependency_response",
            "dependency_fragment",
            "use_fragment",
            "expect_result",
            "actual_result",
            "enable",
            "result",
            "last_execute_time",
            "comment"
        )
        if len(data_return) == len(fileds):
            # 导入namedtuple模块，将数据库返回的值封装在namedtuple模块中，以后可以使用key来访问元组的值
            # 同时也方便维护
            from collections import namedtuple
            chtuple = namedtuple("chtuple", fileds)
            return chtuple._make(data_return)
        else:
            logger.error("The length of namedtuple and mysql is not equal!")
            sys.exit()


test = TestCase()
test.run()
