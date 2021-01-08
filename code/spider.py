import random, time, json
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import schedule
import tushare as ts

class Spider:
    def __init__(self, executable_path):
        self.executable_path = executable_path
        self.url = 'http://quote.eastmoney.com/stocklist.html'

    def get_driver(self):
        USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
        ]
        self.user_agent = random.choice(USER_AGENTS)
        self.headers = {
            'User-Agent': self.user_agent
        }
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('lang=zh_CN.UTF-8')
        self.options.add_argument('start-maximized')
        self.options.add_argument('User-Agent={}'.format(self.user_agent))
        # self.options.add_argument('--headless') # 不弹出浏览器窗口

        driver = webdriver.Chrome(executable_path=self.executable_path, options=self.options)
        script = '''Object.defineProperties(navigator, {webdriver:{get:()=>undefined}})'''
        driver.execute_script(script)
        return driver

    def get_data(self):

        def parse_row(index):
            # index表示处理第几行
            d = {'a': [1,2], 'span': [4,5,6,10,11,12]}
            row = []

            elements = driver.find_elements_by_xpath('//*[@id="table_wrapper-table"]/tbody/tr[{}]/td'.format(index+1))
            for i in range(len(elements)):
                if i not in columns.keys():
                    continue
                if i in d['a']:
                    row.append(str(driver.find_element_by_xpath('//*[@id="table_wrapper-table"]/tbody/tr[{}]/td[{}]/a'.format(index+1, i+1)).text))
                elif i in d['span']:
                    row.append(str(driver.find_element_by_xpath('//*[@id="table_wrapper-table"]/tbody/tr[{}]/td[{}]/span'.format(index+1, i+1)).text))
                else:
                    row.append(str(driver.find_element_by_xpath('//*[@id="table_wrapper-table"]/tbody/tr[{}]/td[{}]'.format(index+1, i+1)).text))
            return row

        data = []

        driver = self.get_driver()
        driver.get(self.url)
        # driver.execute_script('document.documentElement.scrollTop=1000')

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="table_wrapper-table"]')))
        elements = driver.find_elements_by_xpath('//*[@id="table_wrapper-table"]/thead/tr/*')
        columns = []
        for element in elements:
            columns.append(element.find_element_by_xpath('./span').text)
        columns = dict(zip(range(len(columns)), columns))
        columns = {key: val for key, val in columns.items() if val not in ['序号', '相关链接', '加自选']}

        elements = driver.find_elements_by_xpath('//*[@id="table_wrapper-table"]/tbody/tr')
        for index in range(len(elements)):
            row = parse_row(index)
            data.append(row)

        page = 1
        page_num = driver.find_element_by_xpath('//*[@id="main-table_paginate"]/span[1]/a[5]').text

        while page < int(page_num):
            page = page + 1
            driver.find_element_by_xpath('//*[@id="main-table_paginate"]/input').clear()
            driver.find_element_by_xpath('//*[@id="main-table_paginate"]/input').send_keys(page)
            driver.find_element_by_xpath('//*[@id="main-table_paginate"]/a[3]').click()
            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element((By.XPATH, '//*[@id="table_wrapper-table"]/tbody/tr[1]/td[1]'), str((page-1)*20+1)))
            time.sleep(1)

            elements = driver.find_elements_by_xpath('//*[@id="table_wrapper-table"]/tbody/tr')

            for index in range(len(elements)):
                row = parse_row(index)
                data.append(row)

        driver.quit()

        data = pd.DataFrame(data, columns=list(columns.values()))
        return data

def job():
    week = datetime.now().isoweekday()
    if week in [1,2,3,4,5]:
        day = time.strftime('%Y-%m-%d')
        executable_path = '../chromedriver.exe'
        spider = Spider(executable_path)
        data = spider.get_data()
        data.to_csv('../data/{}.csv'.format(day), index=False, encoding='utf_8_sig')

    # data = pd.read_csv('../data/2020-12-29.csv', converters={'代码': str})

if __name__ == '__main__':
    schedule.every().day.at('19:00').do(job)
    while True:
        schedule.run_pending()
        time.sleep(10)

    # job()