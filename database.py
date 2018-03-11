from klein import Klein
from twisted.enterprise import adbapi
import json

class Database(object):

    dbpool = adbapi.ConnectionPool('sqlite3', 'test.db', check_same_thread=False)
    table = 'surveys'

    def _insert(self, cursor, survey_id, survey_json):
        json_str = json.dumps(survey_json)
        insert_stmt = "INSERT INTO surveys VALUES (?, ?);"
        cursor.execute(insert_stmt, (survey_id, json_str))

    def insert(self, survey_id, survey_json):
        return self.dbpool.runInteraction(self._insert, survey_id, survey_json)

    def query(self, survey_id):
        select_stmt = 'SELECT * FROM %s where id="%s"' % (self.table, survey_id)
        return self.dbpool.runQuery(select_stmt)

    def queryAll(self):
        select_stmt = 'SELECT * FROM %s' % (self.table)
        return self.dbpool.runQuery(select_stmt)