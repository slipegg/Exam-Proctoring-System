import pymysql


class DBHelper:
    def __init__(self):
        self.db = None
        self.host = '81.68.125.160'
        self.port = 3306
        self.user = 'root'
        self.password = '123456abcD!'
        self.database = 'user'
        self.table = 'student2'

        self.db = None

    def closeDB(self):
        if self.db is not None:
            self.db.close()
            self.db = None

    def getAllClients(self):
        self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, port=self.port,
                                    database=self.database)
        cursor = self.db.cursor()
        sql = 'select stu_no, stu_name, stu_userlevel, stu_enable from {0} where stu_userlevel = 0'.format(self.table)
        cursor.execute(sql)
        users = cursor.fetchall()

        self.closeDB()

        if len(users) == 0:
            return None
        else:
            return [self.formatUser(user) for user in users]

    def verifyId(self, username, password):
        if username is None or password is None:
            return None
        self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, port=self.port,
                                database=self.database)
        cursor = self.db.cursor()
        sql = 'select stu_no, stu_name, stu_userlevel, stu_enable from {0} where stu_name = %s and stu_password = MD5(%s) and stu_enable = 1'.format(
            self.table)
        value = [username, password]
        cursor.execute(sql, value)
        user = cursor.fetchall()

        self.closeDB()

        if len(user) == 0:
            return None
        else:
            # user is a tuple and the element of it is also tuple.
            return self.formatUser(user[0])

    def formatUser(self, user_tuple):
        """
        for convenience, tag it with dict.
        :param user_tuple: (stu_no, stu_name, stu_userlevel, stu_enable)
        :return:
        """
        print('-----------user_tuple:',user_tuple)
        user_formatted = {'id': user_tuple[0], 'username': user_tuple[1],
                          'is_client': True if user_tuple[2] == '0' else False,
                          'enable_login': True if user_tuple[3] == '1' else False}
        return user_formatted

    def getUsername(self, id):
        self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, port=self.port,
                                database=self.database)
        cursor = self.db.cursor()
        sql = 'select stu_name from {0} where stu_no = %s'.format(
            self.table)
        value = [id]
        cursor.execute(sql, value)
        user = cursor.fetchone()

        self.closeDB()

        if len(user) == 0:
            return None
        else:
            return user[0]

    def modifyPasswd(self, username, old_password, new_password):
        if username is None or old_password is None or new_password is None:
            return False
        self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, port=self.port,
                                database=self.database)
        cursor = self.db.cursor()
        sql = 'select stu_no from {0} where stu_name = %s and stu_password = MD5(%s) and stu_enable = 1'.format(
            self.table)
        value = [username, old_password]
        cursor.execute(sql, value)
        user = cursor.fetchall()

        
        # old username or old password is wrong
        if len(user) == 0:
            self.close()
            return False
        else:
            sql = 'update {0} set stu_password = MD5(%s) where stu_name = %s and stu_password = MD5(%s) and stu_enable = 1'.format(self.table)
            value = [new_password, username, old_password]
            cursor.execute(sql, value)
            self.db.commit()
            self.close()
            return True


db_helper = DBHelper()
