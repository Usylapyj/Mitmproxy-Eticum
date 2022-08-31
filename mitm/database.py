import sqlite3
import hashlib
import json
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('cache.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE  IF NOT EXISTS eticumURLCache (
                                                                    hash TEXT PRIMARY KEY,
                                                                    hostHash TEXT NOT NULL,
                                                                    cache TEXT NOT NULL,
                                                                    ts INTEGER)""")
        self.cursor.execute("""CREATE INDEX  IF NOT EXISTS hostHash ON eticumURLCache (hostHash)""")
        self.cursor.execute("""CREATE INDEX  IF NOT EXISTS uts ON eticumURLCache (ts)""")
        self.conn.commit()
        self.conn.close()

    def add_record(self, url, host, info):
        self.conn = sqlite3.connect('cache.db')
        self.cursor = self.conn.cursor()
        hash_ = hashlib.sha1(url.encode())
        hostHash = hashlib.sha1(host.encode())
        dt = datetime.now()
        ts = datetime.timestamp(dt)
        cache = json.dumps(info)
        self.cursor.execute("INSERT INTO eticumURLCache VALUES(?, ?, ?, ?);", [hash_, hostHash, cache, ts])
        self.conn.commit()
        self.conn.close()

    def clear_old_records(self):
        self.conn = sqlite3.connect('cache.db')
        self.cursor = self.conn.cursor()
        dt = datetime.now()
        old_dt = dt - timedelta(days=2)
        old_ts = datetime.timestamp(old_dt)
        self.cursor.execute("DELETE FROM eticumURLCache WHERE ts < ?", [old_ts])
        self.conn.commit()
        self.conn.close()

    def delete_records_by_host(self, host):
        self.conn = sqlite3.connect('cache.db')
        self.cursor = self.conn.cursor()
        hostHash = hashlib.sha1(host.encode())
        self.cursor.execute("DELETE FROM eticumURLCache WHERE hostHash = ?", [hostHash])
        self.conn.commit()
        self.conn.close()


