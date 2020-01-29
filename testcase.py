import requests
import json
from jsonpath_rw import jsonpath, parse
import re

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
        response = self.run_case(case_id)
        self.write_result(response, case_id)

    def run_case(self, case_id):
        logger.info("Get case id: {}".format(case_id))
        data = self.mysql.get_data_by_id(case_id)
        if data.dependency_id and data.dependency_id.strip():
            data = self.handle_dependency(data)
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
        return response

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
        dependency_id, dependency_fragment, use_fragment = [json.loads(x) for x in (
            data.dependency_id, data.dependency_fragment, data.use_fragment)]
        # 取出三个量的长度，如果不一致，说明输入数据不正确
        lens = map(len, (dependency_id, dependency_fragment, use_fragment))
        if not len(set(lens)) == 1:
            raise FormatError(
                "The length of 'dependency_id, dependency_fragment, use_fragment' of case_id: {} is not equal!\n\
                Filled blank with None if you need not reference dependency response.".format(
                    data.id))
        # 1. 循环执行依赖的case
        # 2. 将依赖的case执行的结果根据dependency_fragment进行处理，包括其中函数的执行
        match_list = []
        for case_id, fragment in zip(dependency_id, dependency_fragment):
            response = self.run_case(case_id)
            match = self.match_result(fragment, response)
            match_list.append(match)
        # 3. 替换data中，数据中包含的需要被替换的变量
        data = self.change_data(data, use_fragment, match_list)
        return data

    #
    # @staticmethod
    # def result(response, data):
    #     if data.expect_result in response.text:
    #         return {"result": "pass"}
    #     else:
    #         return {"result": "fail", "actual_result": response.text}
    #
    # def get_result(self, case_id, response):
    #     return 1

    def write_result(self, response, case_id):
        # 拿到期望结果
        data = self.mysql.get_data_by_id(case_id)
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
                    for expect_key in expect:
                        if expect_key in actual.keys():
                            flag = extractor(expect[expect_key], actual[expect_key])
                            if not flag:
                                return flag
                        else:
                            flag = False
                else:
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
        result = ""
        for frag in fragment:
            # frag: (entity.situation[*], min)
            pattern = frag[0]
            match_list = [match.values for match in parse(pattern).find(response.json)]
            try:
                d = {}
                string = "result = frag[1]({})".format(match_list)
                exec(string, d)
                result = d["result"]
            except IndexError:
                logger.warn("Dependency_fragment: {} not specify function name for match pattern.".format(frag))
            else:
                result = str(match_list).strip("[|]|(|)|{|}")
        return str(result)

    @staticmethod
    def change_data(data, use_fragment, match_list):
        data_return = list(data)
        for index in range(len(data_return)):
            for fragment, match in zip(use_fragment, match_list):
                pattern = re.compile(fragment)
                data_return[index] = pattern.sub(match, data_return[index])
        return data_return


test = TestCase()
test.run()
