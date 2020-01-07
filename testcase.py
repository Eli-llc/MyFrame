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
        url = data[3]
        method = data[4]
        headers = json.loads(data[5])
        payload = data[6]
        if method == "post":
            sr_data = requests.post(url=url, data=payload, headers=headers)
        elif method == "get":
            sr_data = requests.get(url=url, data=payload, headers=headers)
        return sr_data


mysql = MySql()
data = mysql.get_data_by_id(2)
token = "abc"
headers = data[5]
# print(headers["Cookie"])

print(headers)
headers = json.loads(data[5])
print(headers)
