from MySQLCon.mysqlcon import MySql
import requests
import json
import re


class TestCase:
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
data = mysql.get_data_by_id(1)
"""
+------------------------------------+---------------------+-----------------------------------+
| dependency_response                | dependency_fragment | use_fragment                      |
+------------------------------------+---------------------+-----------------------------------+
| {"Cookie":"refiner-token="+$token} | token123            | {"Cookie":"refiner-token=$token"} |
+------------------------------------+---------------------+-----------------------------------+
"""
flag = "abc"
headers = data[10]
dependency_fragment = data[11] # "token"
use_fragment = data[12]
pattern = re.compile(r"\$"+dependency_fragment)
result = re.sub(pattern, flag, use_fragment)
# if "Cookie" in headers.keys():
#     headers["Cookie"] += token
# print(headers, type(headers))
print(result, type(result))
