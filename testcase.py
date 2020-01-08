from MySQLCon.mysqlcon import MySql
import requests
import json


class TestCase:
    """
    执行数据库中的测试用例
    """
    def __init__(self):
        pass

    @staticmethod
    def params():
        mysql = MySql()
        data = mysql.get_data_by_id(1)
        url = data.url
        method = data.method
        headers = json.loads(data.header)
        payload = data.request_data
        if method == "post":
            sr_data = requests.post(url=url, data=payload, headers=headers)
        elif method == "get":
            sr_data = requests.get(url=url, data=payload, headers=headers)
        return sr_data

