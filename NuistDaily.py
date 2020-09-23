import hashlib
import json
import re
import time
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
        self.username = info['username']
        self.password = info['password']
        md5 = hashlib.md5()
        md5.update(self.password.encode('utf-8'))
        self.md5pass = md5.hexdigest()
        self.post_url = "https://client.vpn.nuist.edu.cn:4443/api/enwas/pg/login"
        self.get_url = "https://ssl123xxgg.vpn.nuist.edu.cn/791/list.htm"
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
        self.news_list = {
            '教学考试': [],
            '学院动态': [],
            '校园活动': [],
            '学术报告': [],
            '科研信息': [],
            '专题讲座': [],
            '学术研讨': [],
            '创新创业': [],
            '招生就业': [],
            '其他': [],
            '招标信息': [],
            '党政事务': [],
            '会议通知': [],
            '组织人事': []
        }

    # 先post 再get
    def get_html(self):
        # post 登录
        self.session.post(url=self.post_url,
                          data=json.dumps(self.login_data),
                          headers=self.headers,
                          verify=False,
                          allow_redirects=False)
        # get 获取页面
        html = self.session.get(url=self.get_url,
                                headers=self.headers,
                                verify=False,
                                allow_redirects=False)
        html.encoding = 'utf-8'
        self.html = html.text

    # 正则表达式提取内容
    def get_news(self):
        # 公告整体
        news = re.findall(
            r"<li class=\"news n\d+ clearfix\">(.+?)</li>", self.html)
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
        # 获取全文 TODO 分段
        content = []
        for l in link:
            html = self.session.get(url=l,
                                    headers=self.headers,
                                    verify=False)
            html.encoding = 'utf-8'
            html = html.text
            ct = re.findall(
                r"<div class=\"read\">([\s\S]*?)</div>", html)
            ct = re.findall(
                r">([^>]+?)<", '\n'.join(ct))
            content.append('\n'.join(ct))
            print(l)  # 已爬取的全文
        # 公告日期
        class_news_date = re.findall(
            r"<span class=\"news_date\">(.+?)</span>", '\n'.join(news))
        date = re.findall(
            r"<span class=\"arti_bs\">(\d\d\d\d)\-(\d\d)\-(\d\d)", '\n'.join(class_news_date))
        date = np.array(date)
        year, month, day = date[:, 0], date[:, 1], date[:, 2]  # 年月日
        # 把公告加到 news_list 中
        for d in range(len(date)):
            # 因为一大早可能没有新通知，所以放昨天和今天的
            if day[d] == str(self.today.day) or day[d] == str((self.today + timedelta(days=-1)).day):
                self.news_list[category[d]].append(
                    (title[d], link[d], '-'.join(date[d]), content[d]))

    def make_html(self):
        # 打开文件，准备写入
        f = open(self.TAR_HTML, 'w', encoding='utf-8')
        # HTML头 TODO：可以加样式 style
        message1 = """
        <html>
        <head>
            <meta charset="utf-8">
            <title>NuistDaily</title>
        </head>
        <body>
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
                        "<summary>[" + j[2]+"] " + j[0]+"</summary>" +\
                        j[3]+"</details><hr>"
                message2 += "</details>"
        # 结尾 TODO：可以加脚本 script
        message3 = """
        </body>
        </html>
        """
        # 合并
        message = message1 + message2 + message3
        # 写入文件
        f.write(message)
        f.close()

    def show_html(self):
        # 运行完自动在网页中显示
        webbrowser.open(self.TAR_HTML, new=1)


if __name__ == '__main__':
    spider = NuistDaily()
    spider.get_html()
    spider.get_news()
    spider.make_html()
    spider.show_html()
