import pymysql
import sys

from common.parseyaml import ParseYaml
from common.error import ConfKeyError
from common.log import logger

logger = logger()


class MySql:
    """
    这个类是为了操作数据库
    " 读取数据使用get_data_by_id(id) > TUPLE(CONTENT OF ID)
    " 写入数据使用write_to_mysql(1, {"gender":"5"}) > NONE
        将会更新id为1的行中，gender的字段为5。需要确保数据库有gender字段
    """

    def __init__(self):
        conf_obj = ParseYaml()
        try:
            conf = conf_obj.get_conf("mysql")
            self.host = conf["host"]
            self.port = conf["port"]
            self.user = conf["user"]
            self.password = conf["password"]
            self.database = conf["database"]
            self.table = conf["table"]
        except KeyError as e:
            raise ConfKeyError(e)

    def connect(self):
        """
        这个方法主要是连接数据库，并返回连接对象
        其它方法需要连接数据库时，需要先执行该方法，并拿到连接对象
        """
        # 连接数据库
        try:
            conn = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password,
                                   database=self.database)
            logger.info("Connected to database: {} on {}".format(self.database, self.host))
        except pymysql.err.MySQLError as e:
            logger.error(
                "Connect to database: {} failed, please check you mysql setting...\nOr you can use create_db method.".format(
                    self.database))
            logger.error("MySQLError message: {}".format(e))
            logger.error(
                "Connection info:\n\thost: {host}\n\tuser: {user}\n\tpassword: {password}\n\tdatabase: {database}".format(
                    host=self.host, user=self.user, password=self.password, database=self.database)
            )
            sys.exit()
        return conn

    def get_data_by_id(self, case_id):
        """
        根据给出的case_id，拿到对应行的数据，以元组形式返回
        :param case_id: 
        :return:
        """
        conn = self.connect()
        cursor = conn.cursor()
        sql = "select * from {} where id = {}".format(self.table, case_id)
        logger.info("Execute sql command: {}".format(sql))
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        # 这里fileds是为了给result的每个索引赋值，以后可以通过名字来使用元组中的值
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
        if len(result) == len(fileds):
            # 导入namedtuple模块，将数据库返回的值封装在namedtuple模块中，以后可以使用key来访问元组的值
            # 同时也方便维护
            from collections import namedtuple
            mytuple = namedtuple("mytuple", fileds)
            return mytuple._make(result)
        else:
            logger.error("The length of namedtuple and mysql is not equal!")
            sys.exit()

    def update_mysql(self, case_id, content):
        # 现在只支持通过id写入字典格式的数据
        # 如果后期需要，可以通过id和给出的列表，更新固定的某些列
        logger.info("Write content: {} to case_id: {}".format(content, case_id))
        case_id_content = self.get_data_by_id(case_id)
        entry_len = len(case_id_content)
        if entry_len == 0:
            logger.error("Entry: {} not found.".format(case_id))
            sys.exit(1)
        # 解析输入的content（是一个字典），把每一个键值对根据数据的结构，更新到数据库中。
        # 比如：{"KEY1":"VALUE1"} ,则更新数据库case_id行中，列名为KEY1的列的值为VALUE1
        if not isinstance(content, dict):
            logger.error("Content: {} is not dict.".format(content))
            return
        # 写入数据
        # 获取mysql链接
        elif 0 == len(content):
            logger.warn("The length of content: {} is 0. Need not update.")
            return
        conn = self.connect()
        cursor = conn.cursor()
        # 循环更新传入数据到数据库
        key_value = ["{} = '{}'".format(key, value) for key, value in content.items()]
        update_str = ', '.join(key_value)
        sql = "update {} set {} where id = {};".format(self.table, update_str, case_id)
        logger.info("Execute SQL command: {}".format(sql))
        cursor.execute(sql)
        conn.commit()
        logger.info("Execute SQL command successful!")
        # 关闭连接
        cursor.close()
        conn.close()

    def create_db(self):
        conn = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password)
        cursor = conn.cursor()
        sql = "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET utf8;".format(self.database)
        logger.info("Execute SQL command: {}".format(sql))
        cursor.execute(sql)
        sql = "use {};".format(self.database)
        logger.info("Execute SQL command: {}".format(sql))
        cursor.execute(sql)
        sql = 'CREATE TABLE IF NOT EXISTS {}(\
            id int primary key auto_increment,\
            section varchar(255) not null,\
            case_name varchar(265) not null,\
            url varchar(1023) not null,\
            method varchar(20) not null default "post" check (method in ("post", "get", "delete", "put")),\
            header varchar(255) not null,\
            request_data varchar(2047),\
            file varchar(255),\
            delay int(8) DEFAULT 0,\
            dependency_id varchar(20) default null,\
            dependency_response varchar(512),\
            dependency_fragment varchar(255),\
            use_fragment varchar(255),\
            expect_result varchar(255),\
            actual_result varchar(2047),\
            enable tinyint(1) default 1 check (enable in (0, 1)),\
            result varchar(20),\
            last_execute_time datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\
            comment varchar(255)\
        )CHARACTER SET utf8;\
        '.format(self.table)
        logger.info("Execute SQL command: {}".format(sql))
        cursor.execute(sql)
        conn.commit()
        logger.info("Execute SQL command successful!")
        cursor.close()
        conn.close()

    def get_case_ids(self):
        """
        获取所有的可执行（enabled=1）的case_id
        :return:
        """
        conn = self.connect()
        sql = "select id, enable from {};".format(self.table)
        cursor = conn.cursor()
        logger.info("Execute SQL command: {}".format(sql))
        cursor.execute(sql)
        cases = cursor.fetchall()
        cases_enabled = []
        for case in cases:
            if 1 == case[1]:
                cases_enabled.append(case[0])
        logger.info("The enabled case(s) is(are): {}".format(cases_enabled))
        return cases_enabled
