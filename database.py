from klein import Klein
from twisted.enterprise import adbapi
import json

class Database(object):

    def __init__(self, table):
        self.table = table
        self.dbpool = adbapi.ConnectionPool('sqlite3', 'test.db', check_same_thread=False)

    def _insert(self, cursor, json_id, json_doc):
        json_str = json.dumps(json_doc)
        insert_stmt = "INSERT INTO " + self.table + "  VALUES (?, ?);"
        cursor.execute(insert_stmt, (json_id, json_str))

    def insert_json(self, json_id, json_doc):
        return self.dbpool.runInteraction(self._insert, json_id, json_doc)

    def query(self, id):
        select_stmt = 'SELECT * FROM %s where id="%s"' % (self.table, id)
        return self.dbpool.runQuery(select_stmt)

    def queryAll(self):
        select_stmt = 'SELECT * FROM %s' % (self.table)
        return self.dbpool.runQuery(select_stmt)

