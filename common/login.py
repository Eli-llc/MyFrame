from common.parseyaml import ParseYaml, compose_url
import requests
import json


def _login():
    # 因为大多数测试用例都需要登陆才能执行，所以在common里定义一个登陆系统，并返回cookie给其它用例使用的方法
    parse = ParseYaml()
    conf = parse.get_conf("testSystem")
    url = compose_url("/api/login")
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    payload = json.dumps({"loginName": conf["loginName"], "password": conf["password"]})
    response = requests.post(url=url, data=payload, headers=headers)
    response_dict = json.loads(response.content)
    cookie = {"Cookie": "refiner_access_token=" + response_dict['entity']["hash"]}
    return cookie


cookie = _login()
