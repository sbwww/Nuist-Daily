import hashlib
import json
import re
import time
import urllib
import warnings
import webbrowser
from datetime import date, datetime, timedelta

import numpy as np
import requests

warnings.filterwarnings("ignore")


class NuistDaily(object):
    def __init__(self):
        self.today = date.today()  # 今日日期
        self.TAR_HTML = "NuistDaily.html"  # 命名生成的html
        with open('info.json', 'r') as f:
            info = json.load(f)
        try:
            self.username = info['username']
            self.password = info['password']
            self.last_update = datetime.strptime(
                info['last_update'], '%Y-%m-%d').date()
        except:
            print("info.json 格式错误\n\
                示例：{\"username\": \"201883290000\", \"password\": \"201883290000\", \"last_update\": \"20xx-xx-xx\"}")
        md5 = hashlib.md5()
        md5.update(self.password.encode('utf-8'))
        self.md5pass = md5.hexdigest()
        self.post_url = "https://client.vpn.nuist.edu.cn:4443/api/enwas/pg/login"
        self.get_url_prefix = "https://ssl123xxgg.vpn.nuist.edu.cn/791/list"
        self.get_url_suffix = ".htm"  # FIXME: 1~10页是.htm，后面是.psp
        self.session = requests.session()  # 实例化session会话保持对象
        self.login_data = {
            "name": self.username,
            "password": self.md5pass,
            "t": self.password
        }
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36"
        }
        self.news_list = {  # 可以根据想要看的优先级排序
            '教学考试': [],
            '学院动态': [],
            '校园活动': [],
            '专题讲座': [],
            '学术报告': [],
            '科研信息': [],
            '学术研讨': [],
            '创新创业': [],
            '招生就业': [],
            '其他': [],
            '招标信息': [],
            '党政事务': [],
            '会议通知': [],
            '组织人事': []
        }

    # 先post登录vpn 再get公告内容
    def get_html(self, page):
        # post 登录
        self.session.post(url=self.post_url,
                          data=json.dumps(self.login_data),
                          headers=self.headers,
                          verify=False,
                          allow_redirects=False)
        get_url = self.get_url_prefix+str(page)+self.get_url_suffix
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        # 获取 cookies FIXME: 怎么存？
        with open('js\\set_cookie.js', 'w', encoding='utf-8') as js:
            cookies_message = ""
            for key in cookies_dict:
                cookies_message += key + "=" + cookies_dict[key] + ";"
                js.write(
                    "function set_cookie(){document.cookie = \"" + cookies_message + "\";}")
        # get 获取页面
        html = self.session.get(url=get_url,
                                headers=self.headers,
                                verify=False,
                                allow_redirects=False)
        html.encoding = 'utf-8'
        self.page = html.text

    def check_date(self, news_date):
        # 今天到上一次更新，<= 防止遗漏上次更新当天的内容
        return self.last_update <= news_date

    # 正则表达式提取内容
    def get_news(self):
        # 公告整体
        news = re.findall(
            r"<li class=\"news n\d+ clearfix\">(.+?)</li>", self.page)
        # 是否置顶，用 .*? 因为不置顶的话，中间就是空的
        class_zdtb = re.findall(
            r"<span class=\"zdtb\">(.*?)</span>", '\n'.join(news))
        # 公告类别
        class_wjj = re.findall(
            r"<span class=\"wjj\">(.+?)</span>", '\n'.join(news))
        category = re.findall(
            r"title= '(.+?)'", '\n'.join(class_wjj))
        # 公告标题 正文链接
        class_btt = re.findall(
            r"<span class=\"btt\">(.+?)</span>", '\n'.join(news))
        title = re.findall(
            r"title='(.+?)'", '\n'.join(class_btt))
        link = re.findall(
            r"href='/(.+?)'", '\n'.join(class_btt))
        link = ["https://ssl123xxgg.vpn.nuist.edu.cn/" + l for l in link]
        # 公告日期
        class_news_date = re.findall(
            r"<span class=\"news_date\">(.+?)</span>", '\n'.join(news))
        date = re.findall(
            r"<span class=\"arti_bs\">(.{10,10})", '\n'.join(class_news_date))
        # 获取公告内容，把标题、链接、日期、内容加到 news_list 中
        for d in range(len(date)):
            if class_zdtb[d] != '':
                # 跳过置顶 FIXME: 直接跳过还是其他方法处理
                continue
            if self.check_date(datetime.strptime(date[d], '%Y-%m-%d').date()) == True:
                html = self.session.get(url=link[d],
                                        headers=self.headers,
                                        verify=False)
                html.encoding = 'utf-8'
                html = html.text
                content = re.findall(
                    r"<div class=\"read\">([\s\S]*?)</div></div>", html)
                content = re.findall(
                    r">([^>]+?)<", '\n'.join(content))
                self.news_list[category[d]].append(
                    (title[d], link[d], date[d], '\n'.join(content)))
                print(link[d])
            else:
                return False

    # 根据 news_list 内容生成 html 文件
    def make_html(self):
        # 打开文件，准备写入
        f = open(self.TAR_HTML, 'w', encoding='utf-8')
        # HTML头
        message1 = """
        <html>
        <head>
            <meta charset="utf-8">
            <title>NuistDaily</title>
            <script src="js/set_cookie.js"></script>
        </head>
        <body onload="set_cookie()">
        <a href="https://client.vpn.nuist.edu.cn:4443/client/#/login" rel="noopener noreferrer" target="_blank">vpn</a>
        """
        # 公告部分
        message2 = """
        """
        # 添加公告
        for i in self.news_list:  # 类别
            if len(self.news_list[i]) > 0:  # 只显示有新闻的类别
                message2 += "<details open>" +\
                    "<summary><b>" + i + "</b>" + "&#9;" +\
                    "<font color='red'>" + str(len(self.news_list[i])) + " new</font>" +\
                    "</summary>"
                for j in self.news_list[i]:  # 正文
                    message2 += "<details>" +\
                        "<summary>[" + j[2] + "] " +\
                        "<a href='" + j[1] + "' title='" + j[0] + "'>" +\
                        j[0] + "</a></summary>" +\
                        j[3] + "</details><hr>"
                message2 += "</details>"
        # 结尾
        message3 = """
        </body>
        </html>
        """
        # 合并
        message = message1 + message2 + message3
        # 写入文件
        f.write(message)
        f.close()

    # 运行完自动在浏览器中显示
    def show_html(self):
        webbrowser.open(self.TAR_HTML, new=1)

    # 本次使用日期存入 json
    def update_record(self):
        with open('info.json', 'r+', encoding='utf-8') as f:
            info = json.load(f)
            info["last_update"] = str(self.today)
            f.seek(0)
            json.dump(info, f, ensure_ascii=False)
            f.truncate()


if __name__ == '__main__':
    spider = NuistDaily()
    # 日期超出则停止，最多10页
    for i in range(1, 11):
        spider.get_html(i)
        if spider.get_news() == False:
            break
    else:
        print("距离上次更新太远")
    # 生成 html 并打开
    spider.make_html()
    spider.show_html()
    # 更新日期
    spider.update_record()
