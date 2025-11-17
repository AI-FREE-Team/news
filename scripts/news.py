import os
import time
import requests
from datetime import date, datetime, timezone, timedelta
import re
import pandas as pd
from bs4 import BeautifulSoup
import json

### google trend
start = datetime.now()
print(start)

def web_crawl(weblink):
    headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    }
    res = requests.get(weblink, headers=headers, timeout=5)
    res.encoding = 'UTF-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup

def news_search(keyword, start_date, end_date, n_page, region):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cookie": "AEC=AaJma5vS8teNZfoODOdkgeAAI8gt-rAvzldLxAqOcV4IPiamMHV5zJ3Jbw; NID=526=hZquNpA15B0WkxtHVSzvLusNFCTn68WRJnC1v7oFAOZwilmZNpBshwxMgNm2acHVRbw4rRxqDcoo4oam2bTlFmgl106xKlQquvsFAoR7GghlL_Si9nBhUjNL6jyGwwy9QhPVmFIyRFEjCh9TrZ1LUN3hhGzTAdSdcjEppolkTIJ2PSN4AccxYKYPRr5gBGw55IkbSrKJRAMnwY8XFt7pDbwi22-hfRneKBWQxpFTmGjSDkkca-CxrGxQd0eEY_YbBDr2Uys; DV=I_PHdbaVUqkZ0J-HU_sc0ecSWMYNqRk",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "www.google.hr",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-prefers-color-scheme": "light"
    }
    nums = (n_page-1)*10
    if region == 'TW':
        link = 'https://www.google.hr/search?q=' + keyword + '&lr=lang_zh-TW&hl=en&source=lnms&tbs=cdr:1,cd_min:'+ start_date +',cd_max:'+ end_date + '&tbm=nws&sa=X' + '&start=' + str(nums)
    elif region == 'US':
        link = 'https://www.google.hr/search?q=' + keyword + '&lr=lang_en&hl=en&source=lnms&tbs=cdr:1,cd_min:'+ start_date +',cd_max:'+ end_date + '&tbm=nws&sa=X' + '&start=' + str(nums)

    r = requests.get(link, headers=headers)
    # print(link)
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup
from datetime import datetime, timedelta, timezone
import re

def parse_relative_time_flexible(relative_str, scrape_time=None):
    if scrape_time is None:
        scrape_time = datetime.now(timezone(timedelta(hours=8)))

    text = relative_str.strip().lower()

    # 支援：just now, 1 minute ago, 2 minutes ago, 1 hour ago, ...
    if 'just now' in text or 'few seconds' in text:
        return scrape_time.isoformat()

    # 正則支援單複數
    patterns = [
        (r"(\d+)\s*(minute|minutes)\s*ago", 'minutes'),
        (r"(\d+)\s*(hour|hours)\s*ago", 'hours'),
        (r"(\d+)\s*(day|days)\s*ago", 'days'),
        (r"(\d+)\s*(week|weeks)\s*ago", 'weeks'),
        (r"(\d+)\s*(month|months)\s*ago", 'months'),
        (r"(\d+)\s*(year|years)\s*ago", 'years'),
    ]

    for pattern, unit in patterns:
        match = re.search(pattern, text)
        if match:
            amount = int(match.group(1))
            if unit == 'minutes':
                delta = timedelta(minutes=amount)
            elif unit == 'hours':
                delta = timedelta(hours=amount)
            elif unit == 'days':
                delta = timedelta(days=amount)
            elif unit == 'weeks':
                delta = timedelta(weeks=amount)
            elif unit == 'months':
                delta = timedelta(days=amount * 30)  # 簡化
            elif unit == 'years':
                delta = timedelta(days=amount * 365)
            return (scrape_time - delta).isoformat()

    raise ValueError(f"無法解析時間格式: {relative_str}")

print('【*************Google - 爬蟲開始*************】')

today = datetime.now(timezone(timedelta(hours=8)))
day = timedelta(days=1)
last_7 = today - 1*day

start_date = f'{last_7.month}/{last_7.day}/{last_7.year}'
end_date = f'{today.month}/{today.day}/{today.year}'

ai_keywords = ["AI"]
test = []
for key_word in ai_keywords:

    for language in ['TW', 'US']:
        news_soup = news_search(key_word, start_date, end_date, 1,  region = language)
        one_news = {}
        for j in news_soup.select('.WlydOe'):

            print("【Message】==================================")


            ### 網址
            link_g = j['href']

            ### 新聞來源
            src_g = j.select('span')[0].get_text()

            ### 標題
            title_g = j.select('.MBeuO.nDgy9d')[0].get_text()

            ### 摘要
            try:
              beginning_g = j.select('.nDgy9d')[1].get_text()
            except:
              beginning_g = j.select('.nDgy9d')[0].get_text()

            ### 時間
            published_at = parse_relative_time_flexible(j.select('.LfVVr')[0].get_text())


            try:
                print("【Message】文章連結：", link_g)
                print("【Message】來源：", src_g)
                print("【Message】標題：", title_g)
                print("【Message】摘要：", beginning_g)
                print("【Message】時間：", published_at)
                temp_soup = web_crawl(link_g)
            except:
                print("【Message】連結爬取失敗：", link_g)
                break

            print("【Message】==================================")

            ### 內文
            # selection = 'p'
            # content_g = ''
            # for k in temp_soup.select(selection):
            #     if (len(k.text) > 30) :
            #         content_g += k.text.replace('\x08', '')
            # print(content_g)
            time.sleep(3)

            one_news['title'] = title_g
            one_news['url'] = link_g
            one_news['source'] = src_g
            one_news['published_at'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
            one_news['summary'] = beginning_g
            test.append(one_news)
            one_news = {}

print('【*************Google - 爬蟲結束*************】')
import os

file_path = "tmp/news_batch.json"
os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 自動建立資料夾

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(test, f, ensure_ascii=False, indent=2)

END = datetime.now()
print(END)
print(END-start)
