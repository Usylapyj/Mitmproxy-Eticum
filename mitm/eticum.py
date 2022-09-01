import json
import requests
import sqlite3

class Api:
    def __init__(self):
        self.profileHash = None
        self.profile = None

    def get_tokens(self):
        try:
            conn = sqlite3.connect('auth.db')
            cur = conn.cursor()
            state = cur.execute("SELECT name FROM sqlite_master WHERE type='table' and name='tokens'")
            if state.fetchone():
                e = cur.execute("SELECT value FROM tokens WHERE name='accessToken'")
                accessToken = e.fetchone()
                e = cur.execute("SELECT value FROM tokens WHERE name='refreshToken'")
                refreshToken = e.fetchone()
                return accessToken, refreshToken
            else:
                return None
            cur.close()
            conn.close()
        except sqlite3.Error as error:
            pass

    def update_tokens(self, accessToken, refreshToken):
        try:
            conn = sqlite3.connect('auth.db')
            cur = conn.cursor()
            state = cur.execute("SELECT name FROM sqlite_master WHERE type='table' and name='tokens'")
            if state.fetchone():
                if accessToken:
                    cur.execute(f"UPDATE tokens SET value='{accessToken}' WHERE name='accessToken'")
                if refreshToken:
                    cur.execute(f"UPDATE tokens SET value='{refreshToken}' WHERE name='refreshToken'")
            else:
                cur.execute("CREATE TABLE tokens (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
                if accessToken:
                    cur.execute(f"INSERT INTO tokens (name, value) values('accessToken', '{accessToken}')")
                if refreshToken:
                    cur.execute(f"INSERT INTO tokens (name, value) values('refreshToken', '{refreshToken}')")
            cur.close()
            conn.commit()
            conn.close()
        except sqlite3.Error as error:
            pass

    def auth(self):
        data = {"action": "auth",
                "appVersion": "0.01",
                "platform": "linux"}
        tokens = self.get_tokens()
        if tokens and tokens[0] and tokens[1]:
            data["accessToken"] = tokens[0]
            data["refreshToken"] = tokens[1]
        else:
            data["appName"] = "EticumProxy"
            data["login"] = login
            data["password"] = password
        r = requests.post(ETICUM_URL, data)
        answer = json.loads(r.text)
        if answer["status"] == "authOK":
            accessToken = None
            refreshToken = None
            if "accessToken" in answer.keys():
                accessToken = answer["accessToken"]
            if "refreshToken" in answer.keys():
                refreshToken = answer["refreshToken"]
            if "profileHash" in answer.keys():
                self.profileHash = answer["profileHash"]
                self.profile = answer["profile"]
            self.update_tokens(accessToken, refreshToken)
            return True
        else:
            return False

    def send_keep_alive(self):
        if self.profileHash:
            data = {"action": "online",
                    "accessToken": self.get_tokens()[0],
                    "profileHash": self.profileHash,
                    "cacheTS": 0}
            r = requests.post(ETICUM_URL, data)
            answer = json.loads(r.text)
            if answer["status"] == "onlineOK":
                if "profileHash" in answer.keys():
                    self.profileHash = answer["profileHash"]
                    self.profile = answer["profile"]
                return answer
            elif answer["status"] == "onlineError":
                if "action" in answer.keys() and "action" == "auth":
                    return self.auth()
                else:
                    return False
        else:
            return False

    def info(self, url):
        data = {"action": "info",
                "accessToken": self.get_tokens()[0],
                "url": url}
        r = requests.post(ETICUM_URL, data)
        answer = json.loads(r.text)
        if "info" in answer.keys():
            return answer
        else:
            return False
