import hashlib
import json
import re
import webbrowser
from datetime import date, datetime, timedelta

import numpy as np
import requests


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
            '学术报告': [],
            '招标信息': [],
            '会议通知': [],
            '党政事务': [],
            '组织人事': [],
            '科研信息': [],
            '招生就业': [],
            '教学考试': [],
            '创新创业': [],
            '学术研讨': [],
            '专题讲座': [],
            '校园活动': [],
            '学院动态': [],
            '其他': []
        }

    # 先post 再get
    def get_html(self):
        # post 登录
        self.session.post(url=self.post_url,
                          data=json.dumps(self.login_data),
                          headers=self.headers,
                          verify=False)
        # get 获取页面
        html = self.session.get(url=self.get_url,
                                headers=self.headers,
                                verify=False)
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
            r"href='(.+?)'", '\n'.join(class_btt))
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
                    (title[d], link[d], day[d]))

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
        <a href="https://ssl123xxgg.vpn.nuist.edu.cn/791/list.htm" rel="noopener noreferrer" target="_blank">信息公告</a>
        """
        # 公告部分
        message2 = """
        """
        # 添加公告
        for i in self.news_list:
            if len(self.news_list[i]) > 0:
                message2 += "<details open><summary>" + \
                    "<b>" + i + "</b>" + "&#9;" + \
                    "<font color='red'>" + \
                    str(len(self.news_list[i])) + " new</font></summary>"
                for j in self.news_list[i]:
                    message2 += "<li><a href='https://ssl123xxgg.vpn.nuist.edu.cn/" + \
                        j[1]+"' target='_blank' title='" + \
                        j[2]+"日'>"+j[0]+"</a></li>"
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
        # 运行完自动在网页中显示
        webbrowser.open(self.TAR_HTML, new=1)


if __name__ == '__main__':
    spider = NuistDaily()
    spider.get_html()
    spider.get_news()
    spider.make_html()
