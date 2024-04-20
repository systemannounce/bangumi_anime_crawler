import os
import sys
import re
import csv
import requests
from lxml import etree
import random
import fcntl
import time
import threading


def welcome():
    print('''
这个程序是为了各位可以方便快速排出当前所有番剧在bangumi网站的排名而诞生的。
如果你只需要知道某个番剧的排名和评分只需要自行去https://bangumi.tv自行查询
请勿对本程序滥用！！！
请确保自身网络可以正常访问bangumi.tv网站，否则会出错
爬取过程中，请不要对着程序乱按，卡住一小段时间为正常情况，否则容易崩溃。
如果你继续操作将视为同意以上内容。''')


class MainFunction():
    def __init__(self, master=None):
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
        self.re_request = False  # 跳过解析
        self.status = True
        self.addrow = False

        self.interrupt()  # 调用中断查询

        self.main()

    def main(self):
        # 创建并启动多个线程
        threads = []
        for page_gather in range(1, int(self.read_page())):  # 此处更改爬取页数，因为是异步所以难做自动停止。
            for page in range(10 * (page_gather - 1) + 1, 10 * page_gather + 1):
                t = threading.Thread(target=self.bangumi_requests, args=(page,))
                threads.append(t)
                t.start()
            time.sleep(random.randint(3, 8))

        for t in threads:
            t.join()
        self.re_sort()

    def re_sort(self):
        with (open('./systemannounce_anime.csv', 'r', encoding='utf-8') as file1,
              open('./systemannounce_anime.txt', 'r', encoding='utf-8') as file2):
            csv_reader = csv.reader(file1)
            data1 = [[int(x) if i == 0 else x for i, x in enumerate(row)] for row in csv_reader]
            data2 = file2.readlines()
        sorted_data1 = sorted(data1, key=lambda x: x[0])
        sorted_data2 = sorted(data2, key=lambda x: int(x.split('|')[0]))
        header1 = ['rank', 'anime', 'date', 'score']
        header2 = 'rank|anime|date|score\n'
        # 打开新的 CSV 文件进行写入
        with (open('./systemannounce_anime.csv', 'w', newline='') as csv_file,
              open('./systemannounce_anime.txt', 'w', newline='') as txt_file):
            csv_writer = csv.writer(csv_file)

            # 写入标题行(可选)
            if header1:
                csv_writer.writerow(header1)
            if header2:
                txt_file.write(header2)

            # 写入排序后的数据
            csv_writer.writerows(sorted_data1)
            txt_file.writelines(sorted_data2)

    def interrupt(self):
        if os.path.isfile('./systemannounce_anime.csv'):
            os.remove('./systemannounce_anime.csv')
            if os.path.isfile('./systemannounce_anime.txt'):
                os.remove('./systemannounce_anime.txt')  # 设计上两个文件相辅相成，同时进行操作.
            self.addrow = True

    def log_message(self, message):
        print(message)

    def read_page(self):
        with open('./page.txt', 'r', encoding='utf-8') as f:
            return re.sub(r'[\s\n\t]+', '', f.read())

    def bangumi_requests(self, line_num):
        if self.status:
            self.log_message('Crawling page {}...'.format(line_num))
            self.param = {
                "sort": "rank",
                "page": line_num
            }
            self.exception = False
            self.re_request = True
            while (self.re_request):
                try:
                    respond = requests.get(url=self.url, headers=self.headers, params=self.param)
                    self.re_request = False
                    self.exception = False
                except:
                    self.exception = True
                    self.count = self.count + 1
                    rerr = 'Request wrong , retrying... ' + '\n' + str(self.count) + ' time(s)\n'
                    time.sleep(random.randint(3, 10))
                    self.log_message(rerr)
                    if self.count >= 10:
                        enderr = 'Request ERROR in page ' + str(line_num) + '\nIGNORE THIS PAGE\n'
                        self.log_message(enderr)
                        print(enderr + '\n')
                        self.re_request = False  # 跳过下面解析
                        self.count = 0
                        line_num = line_num + 1

            if not self.exception:
                self.count = 0
                try:
                    respond.encoding = respond.apparent_encoding
                    respon_text = respond.text
                    tree = etree.HTML(respon_text, etree.HTMLParser())
                    titles = tree.xpath('//ul[@id="browserItemList"]//a[@class="l"]/text()')
                    score = tree.xpath('//small[@class="fade"]/text()')
                    page_dates = tree.xpath('//*[@id="browserItemList"]/li/div/p[1]/text()')
                    anime_dates_list = []  # 进入循环前先清空列表
                    for one_dates in page_dates:
                        anime_date = re.search(r'\d{4}年(\d{1,2}月\d{1,2}日)?|\d{4}-\d{1,2}-\d{1,2}|\d{4}', one_dates)
                        if anime_date:
                            anime_dates_list.append(anime_date.group())
                        else:
                            anime_dates_list.append('None')
                except:
                    ler = 'lxml ERROR in' + str(line_num) + '\nExiting...'
                    self.log_message(ler)
                    print(ler + '\n')
                    raise Exception('lxml err')
                    exit()
                if len(titles) == 0 and len(score) == 0:
                    finish = '爬取结束，一共爬取了' + str(line_num - 1) + '页'
                    print(finish)
                    sys.exit()

                with (open('./systemannounce_anime.csv', 'a', encoding='utf-8', newline='') as f1,
                      open('./systemannounce_anime.txt', 'a', encoding='utf-8') as f2):
                    # 获取文件锁
                    fcntl.flock(f1.fileno(), fcntl.LOCK_EX)
                    fcntl.flock(f2.fileno(), fcntl.LOCK_EX)
                    writer = csv.writer(f1)
                    for num, ti in enumerate(titles):
                        content = str((line_num - 1) * 24 + num + 1) + '|' + ti + '|' + anime_dates_list[num] + '|' + \
                                  score[num] + '\n'
                        f2.write(content)
                        title = re.sub(r'[,"]', ' ', ti)  # 为了适应GitHub的CSV文件标准
                        writer.writerow([str((line_num - 1) * 24 + num + 1), title, anime_dates_list[num], score[num]])
                    # 释放文件锁
                    fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
                    fcntl.flock(f2.fileno(), fcntl.LOCK_UN)


if __name__ == '__main__':
    respond = None
    welcome()
    app = MainFunction()
