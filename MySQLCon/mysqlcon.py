import pymysql
import sys
import common.parseyaml


class MySql:
    """
    这个类是为了操作数据库
    " 读取数据使用get_data_by_id(id) > TUPLE(CONTENT OF ID)
    " 写入数据使用write_to_mysql(1, {"gender":"5"}) > NONE
        将会更新id为1的行中，gender的字段为5。需要确保数据库有gender字段
    """

    def __init__(self):
        conf_obj = common.parseyaml.ParseYaml()
        conf = conf_obj.get_conf("mysql")
        self.host = conf["host"]
        self.port = conf["port"]
        self.user = conf["user"]
        self.password = conf["password"]
        self.database = conf["database"]
        self.table = conf["table"]

    def connect(self):
        """
        这个方法主要是连接数据库，并返回连接对象
        其它方法需要连接数据库时，需要先执行该方法，并拿到连接对象
        """
        # 连接数据库
        try:
            conn = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password,
                                   database=self.database)
        except pymysql.err.MySQLError as e:
            print("Connect to database failed, please check you mysql setting...\nOr you can use create_db method.")
            print("MySQLError message: {}".format(e))
            print("Connection info:\n\thost: {host}\n\tuser: {user}\n\tpassword: {password}\n\tdatabase: {database}" \
                  .format(host=self.host, user=self.user, password=self.password, database=self.database)
                  )
            sys.exit()
        return conn

    def get_data_by_id(self, case_id):
        conn = self.connect()
        cursor = conn.cursor()
        sql = "select * from {} where id = {}".format(self.table, case_id)
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result

    def write_to_mysql(self, case_id, content):
        # 现在只支持通过id写入字典格式的数据
        # 如果后期需要，可以通过id和给出的列表，更新固定的某些列
        case_id_content = self.get_data_by_id(case_id)
        entry_len = len(case_id_content)
        if entry_len == 0:
            print("Entry not found.")
            sys.exit(1)
        elif entry_len > 1:
            print("Too many entries match.")
            sys.exit(1)
        # 解析输入的content（是一个字典），把每一个键值对根据数据的结构，更新到数据库中。
        # 比如：{"KEY1":"VALUE1"} ,则更新数据库case_id行中，列名为KEY1的列的值为VALUE1
        if not isinstance(content, dict):
            print("Input data is not dict.")
            sys.exit(2)
        # 写入数据
        # 获取mysql链接
        conn = self.connect()
        cursor = conn.cursor()
        # 循环更新传入数据到数据库
        key_value = ['{} = "{}"'.format(key, value) for key, value in content.items()]
        update_str = ', '.join(key_value)
        if len(update_str) >= 3:
            sql = "update {} set {} where id = {};".format(self.table, update_str, case_id)
            cursor.execute(sql)
            conn.commit()
        else:
            print("update string no set params.\nCancel operation.")

        # 关闭连接
        cursor.close()
        conn.close()

    def create_db(self):
        conn = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password)
        cursor = conn.cursor()
        sql = "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET utf8;".format(self.database)
        cursor.execute(sql)
        sql = "use {};".format(self.database)
        cursor.execute(sql)
        sql = """CREATE TABLE IF NOT EXISTS testcases(\
            id int primary key auto_increment,\
            section varchar(255) not null,\
            case_name varchar(265) not null,\
            url varchar(512) not null,\
            method varchar(20) not null default "post" check (method in ("post", "get", "delete", "put")),\
            header varchar(255) not null,\
            request_data varchar(255),\
            file varchar(255),\
            delay int(8) DEFAULT 0,
            dependency_id int default null,\
            dependency_response varchar(512),\
            dependency_fragment varchar(255),\
            use_fragment varchar(255),\
            expect_result varchar(255),\
            actual_result varchar(255),\
            enable tinyint(1) default 1 check (enable in (0, 1)),\
            result varchar(20),\
            comment varchar(255)
        )CHARACTER SET utf8;
        """
        cursor.execute(sql)
        # url = common.parseyaml.compose_url("/api/login")
        # sql = "INSERT INTO testcases VALUES(NULL, {}, {}, {url}, {method}, {header}, {request_data}, {delay},\
        # {dependency_id}, {dependency_response}, {dependency_fragment}, {use_fragment}, {expect_result},\
        # {actual_result}, {enable}, {result}, {comment});\"" \
        #       ".format("登陆", "登陆", url=url, method="post", header )
        # cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
