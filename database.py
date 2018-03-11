from klein import Klein
from twisted.enterprise import adbapi
import json

class Database(object):

    dbpool = adbapi.ConnectionPool('sqlite3', 'test.db', check_same_thread=False)
    table = 'surveys'

    def _insert(self, cursor, survey_id, survey_json):
        insert_stmt = 'insert into %s (id, data) values ("%s", "%s")' % (self.table, survey_id, json.dumps(survey_json))
        cursor.execute(insert_stmt)

    def insert(self, survey_id, survey_json):
        return self.dbpool.runInteraction(self._insert, survey_id, survey_json)

    def queryAll(self):
        select_stmt = 'SELECT * FROM %s' % (self.table)
        return self.dbpool.runQuery(select_stmt)