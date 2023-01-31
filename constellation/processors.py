import duckdb
from .pipeline import Msg
import logging

log = logging.getLogger(__name__)


class DuckDBProcessor:
    def __init__(self, tags=[]):
        self.con = duckdb.connect(database='duck.db')
        self.con.execute("""
        CREATE TABLE measurements (
            measurement STRING,
            ts DATETIME,
            value DOUBLE
        )""")

        self.tags = tags
        for tag in self.tags:
            self.con.execute(f"""
            ALTER TABLE measurements ADD COLUMN {tag} STRING
            """)

    def msgToRow(self, msg: Msg):
        yield "'" + str(msg.measurement) + "'"
        yield "'" + str(msg.timestamp) + "'"
        yield str(msg.value)

        for tag in self.tags:
            if tag in msg.tags:
                yield "'" + msg.tags.get(tag) + "'"
            else:
                yield 'NULL'

    def __call__(self, msg: Msg):
        query = f"insert into measurements values ({','.join(self.msgToRow(msg))})"
        log.debug(f"Execute query: \"{query}\"")
        self.con.execute(query)


