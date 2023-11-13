import os
import sys
import requests
from lxml import etree
import random
import tkinter as tk
from tkinter import messagebox


def welcome():
    eula = messagebox.askyesno(title='EULA', message='''
这个程序是为了各位可以方便快速排出当前所有番剧在bangumi网站的排名而诞生的。PS:最大页数999页
如果你只需要知道某个番剧的排名和评分只需要自行去https://bangumi.tv自行查询
请勿对本程序滥用！！！
请确保自身网络可以正常访问bangumi.tv网站，否则会出错
爬取过程中，请不要对着程度乱按，卡住一小段时间为正常情况，否则容易崩溃。
接受请按是(YES)。''')
    print(eula)
    return eula


class MainFunction(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.current = 1
        self.url = 'https://bangumi.tv/anime/browser'
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 '
                'Safari/537.36'
        }
        self.lines = None  # 中断行
        self.answer = None  # 用户选择
        """下面是主程序声明处"""
        self.respond = None
        self.exception = None
        self.count = 0

        self.interrupt()  # 调用中断查询
        self.create_ui()
        pass

    def log_message(self, message):
        self.logbox.config(state='normal')
        self.logbox.insert(tk.END, message + '\n')
        self.logbox.config(state='disabled')

    def timed_event(self):
        self.log_message('Crawling page {}\n'.format(self.current))
        self.bangumi_requests()
        self.master.after(random.randint(1000, 15000), self.timed_event)

    def create_ui(self):
        self.refresh = tk.StringVar()
        self.refresh.set('当前进度：N/A')
        self.label01 = tk.Label(self, textvariable=self.refresh, fg='white', bg='black',
                                font=('微软雅黑', '20'))
        self.label01.pack(side='top')

        self.logbox = tk.Text(self)
        self.logbox.pack()

    def update(self):
        self.refresh.set('当前进度：{}'.format(self.current))

    def interrupt(self):
        """中断查询函数，查询用户是否有过使用本程序"""
        if os.path.isfile('./anime.txt'):
            with open('./anime.txt', 'r', encoding='utf-8') as f:
                self.lines = len(f.readlines())
            self.answer = messagebox.askyesno(title='中断提醒',
                                              message='你上次在第{}行的时候中断，请问要从断点处继续吗？'.format(
                                                  self.lines))
            if self.answer:
                self.current = int(self.lines / 24 + 1)

    def bangumi_requests(self):
        self.update()
        self.param = {
            "sort": "rank",
            "page": self.current
        }
        self.exception = False
        try:
            respond = requests.get(url=self.url, headers=self.headers, params=self.param)
        except:
            self.exception = True
            self.count = self.count + 1
            rerr = 'request wrong , retrying...' + str(self.count) + 'time(s)'
            self.log_message(rerr)
            if self.count >= 10:
                self.exception = False
                enderr = 'request ERROR in' + str(self.current) + 'page'
                self.log_message(enderr)
                print(enderr)
        if not self.exception:
            self.count = 0

            respond.encoding = respond.apparent_encoding
            respon_text = respond.text
            try:
                tree = etree.HTML(respon_text)
                title = tree.xpath('//ul[@id="browserItemList"]//a[@class="l"]/text()')
                score = tree.xpath('//small[@class="fade"]/text()')
            except:
                ler = 'lxml ERROR in' + str(self.current) + '\n'
                self.log_message(ler)
                print(ler)
            if len(title) == 0 and len(score) == 0:
                finish = '爬取结束，一共爬取了' + str(self.current - 1) + '页'
                messagebox.showinfo(title='结束', message=finish)
                print(finish)
                sys.exit()
            with open('./anime.txt', 'a', encoding='utf-8') as f:
                for num, ti in enumerate(title):
                    # print(ti , '' , score[num])
                    content = ti + '|' + score[num] + '\n'

                    f.write(content)
                    # f.write('\n')
                # print(title)
            print(self.current)
            self.current = self.current + 1


if __name__ == '__main__':
    respond = None
    root = tk.Tk()
    root.geometry('300x500+100+200')
    root.title('bangumi番剧爬取工具,MADE WITH LOVE')
    if not welcome():
        sys.exit()
    app = MainFunction(master=root)
    app.timed_event()
    root.mainloop()