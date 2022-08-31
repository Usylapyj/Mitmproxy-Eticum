from mitmproxy import ctx
from mitmproxy import http
from mitmproxy.script import concurrent
import eticum
from urllib.parse import urlparse
import re
from threading import Thread
import time
import database

class Filter:
    class KeepAliveThread(Thread):
        def __init__(self, root):
            super().__init__()
            self.root = root

        def run(self):
            while True:
                keep_alive_answer = self.root.api.send_keep_alive()
                if keep_alive_answer:
                    if "payload" in keep_alive_answer.keys():
                        if "clearCache" in keep_alive_answer["payload"].keys():
                            for host in keep_alive_answer["payload"]["clearCache"]:
                                self.root.database.delete_records_by_host(host)
                ctx.log.info(">>>> keep_alive sended " + str(self.root.api.send_keep_alive()))
                time.sleep(120)

    class UpdateDatabaseThread(Thread):
        def __init__(self, root):
            super().__init__()
            self.root = root

        def run(self):
            while True:
                n = self.root.database.clear_old_records()
                time.sleep(300)
                
    def __init__(self):
        self.api = eticum.Api()
        self.api.auth()
        self.database = database.Database()
        self.ignored_hosts = [
                "info.eticum.com",
                "info-dev.eticum.com",
                "www.eticum.com",
                "app.eticum.com"
                ]
        self.yandex_hosts = [
                "yandex.tm",
                "yandex.tj",
                "yandex.eu",
                "yandex.az",
                "yandex.uz",
                "yandex.ee",
                "yandex.lt",
                "yandex.lv",
                "yandex.md",
                "yandex.by",
                "yandex.ua",
                "yandex.com"]
        self.other_search_hosts = [
                "www.google.com",
                "www.google.ru",
                "www.bing.com"
                ]
        self.yandex_paths = [
                "/search",
                "/images",
                "/images/search",
                "/video/search"
                ]
        self.keep_alive_thread = self.KeepAliveThread(self)
        self.keep_alive_thread.start()
        self.update_database_thread = self.UpdateDatabaseThread(self)
        self.update_database_thread.start()

    @concurrent
    def request(self, flow):
        if flow.request.pretty_host in self.ignored_hosts:
            return
        if self.api.profile:
            if self.api.profile["mode"] in ["info", "bypass"]:
                return
            if "allow" in self.api.profile.keys():
                for s in self.api.profile["allow"]:
                    if flow.request.url.startswith(s):
                        return
        path = urlparse(flow.request.url).path
        if flow.request.path_components:
            if flow.request.path_components[-1] == "wpad.dat":
                return
            if flow.request.path_components[-1].split(".")[-1] in ["css", "js", "ico"]:
                return
        if self.api.profile:
            if "deny" in self.api.profile.keys():
                if flow.request.scheme + "://" + flow.request.pretty_host in self.api.profile["deny"]:
                    flow.response = http.Response.make(200, b"Blocked", {"Content-Type": "text/html"})
            if self.api.profile["filterWords"] and "words" in self.api.profile.keys():
                for s in self.api.profile["words"]:
                    pattern = re.compile(s)
                    result = pattern.subn("*"*len(s), flow.request.url)
                    if result[1]:
                        flow.request.url = result[0]
            info = self.api.info(flow.request.url)
            if "status" in info["info"].keys() and info["info"]["status"] == "no data":
                if self.api.profile["mode"] == "allow":
                    flow.response = http.Response.make(200, b"Blocked", {"Content-Type": "text/html"})
            else:
                if self.api.profile["mode"] in ["allow", "deny"]:
                    if info["info"]["age"] > self.api.profile["age"]:
                        flow.response = http.Response.make(200, b"Blocked", {"Content-Type": "text/html"})
                        return
                if "categories" in info["info"]:
                    flag = True
                    if self.api.profile["mode"] == "allow":
                        for i in info["info"]["categories"]:
                            if not i in self.api.profile["categories"]:
                                flag = False
                                break
                    if self.api.profile["mode"] == "deny":
                        for i in info["info"]["categories"]:
                            if i in self.api.profile["categories"]:
                                flag = False
                                break
                    if not flag:
                        flow.response = http.Response.make(200, b"Blocked", {"Content-Type": "text/html"})
                        return
        if flow.request.host in self.yandex_hosts:
            if path in self.yandex_paths:
                flow.request.query["family"] = "yes"
        if flow.request.pretty_host in self.other_search_hosts:
            if path == "/search":
                flow.request.query["safe"] = "active"


    @concurrent
    def response(self, flow):
        if flow.request.pretty_host in self.ignored_hosts:
            return
        if self.api.profile:
            if self.api.profile["mode"] in ["info", "bypass"]:
                return
            if "allow" in self.api.profile.keys():
                for s in self.api.profile["allow"]:
                    if flow.request.url.startswith(s):
                        return
        path = urlparse(flow.request.url).path
        if flow.request.path_components:
            if flow.request.path_components[-1] == "wpad.dat":
                return
            if flow.request.path_components[-1].split(".")[-1] in ["css", "js", "ico"]:
                return
        if flow.response.status_code > 300 and flow.response.status_code < 400:
            return
        try:
            content = flow.response.content.decode()
        except UnicodeDecodeError:
            ctx.log.info("Can't decode response content")
            return
        if self.api.profile["filterWords"] and "words" in self.api.profile.keys():
            for s in self.api.profile["words"]:
                pattern = re.compile(s)
                result = pattern.subn("*"*len(s), content)
                if result[1]:
                    content = result[0]
        flow.response.content = content.encode()







addons = [
    Filter()
]
