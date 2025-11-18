import os
import time
import requests
from datetime import date, datetime, timezone, timedelta
import re
import pandas as pd
from bs4 import BeautifulSoup
import json
from zoneinfo import ZoneInfo

sera_token = os.getenv("SERA_TOKEN")
### google trend
start = datetime.now()
print(start)

def sera_google_search(keyword, start_date, end_date):
  params = {
      "engine": "google",
      "q": keyword,
      "gl": "tw",
      "hl": "zh-tw",
      "tbm": "nws",
      "time_range": "Custom",
      "start_date": start_date,
      "end_date": end_date,
      "api_key": sera_token
      }
  url = "https://serpapi.com/search"
  r = requests.get(url, params=params)
  return r.json()


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
last_day = today - 1*day
last_day2 = today - 2*day

start_date = f'{last_day2.month}/{last_day2.day}/{last_day2.year}'
end_date = f'{last_day.month}/{last_day.day}/{last_day.year}'

ai_keywords = ["AI"]
test = []
for key_word in ai_keywords:

    for language in ['TW']:
        # news_soup = news_search(key_word, start_date, end_date, 1,  region = language)
        news_soup = sera_google_search(key_word, start_date, end_date)

        all_news = []

        for i in news_soup['news_results']:
          if 'stories' in i:
            for j in i['stories']:
              all_news.append(j)
          else:
            all_news.append(i)

        for i in all_news:
          one_news = {}
          link_g = i['link']
          src_g = i['source']
          title_g = i['title']
          beginning_g = i['snippet']
          published_at = i['published_at']

          one_news['title'] = title_g
          one_news['url'] = link_g
          one_news['source'] = src_g
          one_news['published_at'] = str(datetime.strptime(published_at.replace(' UTC', ''), '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Taipei")))
          one_news['summary'] = beginning_g
          test.append(one_news)


print('【*************Google - 爬蟲結束*************】')
import os

file_path = "tmp/news_batch.json"
os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 自動建立資料夾

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(test, f, ensure_ascii=False, indent=2)

END = datetime.now()
print(END)
print(END-start)
