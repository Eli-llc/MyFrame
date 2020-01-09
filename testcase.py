import requests
import json

from MySQLCon.mysqlcon import MySql
from common.login import cookie
from common.parseyaml import compose_url


class TestCase:
    """
    执行数据库中的测试用例
    """

    def __init__(self):
        self.mysql = MySql()

    def run(self):
        # 拿到所有可执行case的ID，然后逐个执行
        cases_enabled = self.mysql.get_case_ids()
        for case in cases_enabled:
            self.run_case(case)

    def run_dependence(self, dependence):
        # 执行依赖的用例
        # 这里依赖的用例可能是1个，也可能是多个，建议1个依赖单个值传递，多个依赖以可迭代方式传递，包括列表，元组，集合等
        # 单个依赖
        if int is type(dependence) or tuple is type(dependence):
            response = self.run_case(dependence)
        # 多个依赖
        elif list is type(dependence) or set is type(dependence) or hasattr(dependence, "__iter__"):
            dependence_list = dependence
            response = []
            for dependence in dependence_list:
                temp = self.run_case(dependence)
                response.append(temp)
        # 错误
        else:
            response = None
        return response

    def match_dependence(self, dependence_string, dependence_fragment):
        # 提取规则和被匹配的字符串，返回匹配结果
        result = dependence_fragment, dependence_string
        return result

    def change_params(self, match_fragment, data):
        # 更改数据库中含有的变量
        return data

    def run_case(self, case_id):
        # 通过case_id来执行具体的用例
        print("Now execute case: {}".format(case_id))
        data = self.mysql.get_data_by_id(case_id)
        dependence = data.dependency_id
        dependence_fragment = data.dependency_fragment
        # 拿到依赖的case返回的参数
        dependence_string = self.run_dependence(dependence)
        # 拿到匹配结果
        match_fragment = self.match_dependence(dependence_string, dependence_fragment)
        # 根据匹配的参数，以及希望替换的值，替换掉数据库中的指定字段，然后重新赋值给data
        data = self.change_params(match_fragment, data)
        url = compose_url(data.url)
        method = data.method
        headers = json.loads(data.header)
        headers.update(cookie)
        payload = data.request_data
        files = data.file or None
        if files:
            # 这里使用了exec函数，必须按照下面的方式，才能将数据库中files中的open函数执行。否则会出现ValueError
            # ValueError: cannot encode objects that are not 2-tuples
            # 下面s是exec执行的python语句。d是exec的一个命名空间，exec执行的结果将存放在这个字典中，
            # 然后在外面使用这个字典，才可以取出files的值
            s = "files = {}".format(files)
            d = {}
            exec(s, d)
            files = d["files"]
        if method == "post":
            response = requests.post(url=url, data=payload, headers=headers, files=files)
        elif method == "get":
            response = requests.get(url=url, data=payload, headers=headers, files=files)
        elif method == "delete":
            response = requests.delete(url=url, data=payload, headers=headers)
        else:
            print("Method: {} not support!".format(method))
            result = {"result": "failed"}
            self.mysql.write_to_mysql(case_id, result)
            return
        # 拿到要写入数据库的结果，即case执行结束后，需要写入数据库的内容
        result = self.result(response, data)
        # 写入结果到数据库
        self.mysql.write_to_mysql(case_id, result)
        return response

    @staticmethod
    def result(response, data):
        # 返回写入数据库的内容
        if data.expect_result in response.text:
            return {"result": "pass"}
        else:
            return {"result": "fail", "actual_result": response.text}


test = TestCase()
test.run()
