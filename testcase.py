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
        cases_enabled = self.mysql.get_case_ids()
        for case in cases_enabled:
            self.run_case(case)

    def run_case(self, case_id):
        print("Now execute case: {}".format(case_id))
        data = self.mysql.get_data_by_id(case_id)
        url = compose_url(data.url)
        method = data.method
        headers = json.loads(data.header)
        headers.update(cookie)
        payload = data.request_data
        files = data.file or None
        if case_id == 3:
            files = "files = {}".format(files)
            print(files)
            exec(files)
            print(files, type(files))
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
        result = self.result(response, data)
        self.mysql.write_to_mysql(case_id, result)

    @staticmethod
    def result(response, data):
        if data.expect_result in response.text:
            return {"result": "pass"}
        else:
            return {"result": "fail", "actual_result": response.text}


test = TestCase()
test.run()
