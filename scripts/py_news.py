import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from g4f.client import Client

# 設定時區
TAIPEI = ZoneInfo("Asia/Taipei")

# Helper 函數：載入 JSON 檔案
def load_json(path):
  if not os.path.exists(path):
    print(f"Warning: File not found at {path}. Returning empty list.")
    return []
  with open(path, "r", encoding="utf-8") as f:
    try:
      return json.load(f)
    except json.JSONDecodeError:
      print(f"Error: JSONDecodeError in file {path}. Backing up and returning empty list.")
      backup = path + ".corrupt"
      os.replace(path, backup)
      return []

# Helper 函數：儲存 JSON 檔案
def save_json(path, data):
  os.makedirs(os.path.dirname(path), exist_ok=True) # 確保目錄存在
  with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 1. 計算昨日日期
    today_dt = datetime.now(TAIPEI).date()
    yesterday_dt = today_dt - timedelta(days=1)
    yesterday_iso = yesterday_dt.isoformat() # YYYY-MM-DD 格式

    # 2. 讀取 data/ 資料夾中的昨日 JSON 檔案
    data_dir = "data"
    yesterday_data_path = os.path.join(data_dir, f"{yesterday_iso}.json")
    print(f"Attempting to load data from: {yesterday_data_path}")
    articles = load_json(yesterday_data_path)

    if not articles:
        print("No articles found for yesterday. Exiting.")
        # 即使沒有文章，也要生成一個空的電子報檔案，避免 workflow 失敗
        md_filename = os.path.join("eletters", f"{today_dt.isoformat()}.md")
        os.makedirs(os.path.dirname(md_filename), exist_ok=True)
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(f"# {today_dt.strftime('%Y年%m月%d日')} 每日電子報\n\n")
            f.write("抱歉，沒有找到昨日的文章資料來生成電子報。\n")
        return

    # 3. 只抓取 'title' 和 'summary' 變成一個新的列表
    filtered_data = []
    for article in articles:
        if 'title' in article and 'summary' in article:
            filtered_data.append({
                "title": article["title"],
                "summary": article["summary"]
            })
    
    if not filtered_data:
        print("No valid title or summary found in yesterday's data. Exiting.")
        # 同樣，生成一個空的電子報檔案
        md_filename = os.path.join("eletters", f"{today_dt.isoformat()}.md")
        os.makedirs(os.path.dirname(md_filename), exist_ok=True)
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(f"# {today_dt.strftime('%Y年%m月%d日')} 每日電子報\n\n")
            f.write("抱歉，昨日的文章資料中沒有找到有效的標題或摘要。\n")
        return

    # 準備給 LLM 的 prompt
    prompt_parts = [f"你是一個專業的 AI 產業專家，經營一個專業的粉絲社群，依據最新的AI重點新聞，每天會去撰寫分享AI趨勢洞察的AI重點摘要文章跟評比。 請根據以下內容，生成一份關於 {yesterday_dt.strftime('%Y年%m月%d日')} 的每日 AI 趨勢的社群文章。"]
    for i, item in enumerate(filtered_data):
        prompt_parts.append(f"## 文章 {i+1}: {item['title']}")
        prompt_parts.append(f"摘要: {item['summary']}")
    prompt_parts.append("\n請以 Markdown 格式輸出，包含標題和重點摘要，請加入Emoji、排版要可以讓文章閱讀更方便。")
    prompt = "\n".join(prompt_parts)

    print("Sending prompt to LLM...")
    # 4. 透過 g4f 進行推論
    try:
        client = Client() # 每次執行時重新初始化，確保是最新狀態
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 這裡可以根據您的需求指定模型
            messages=[{"role": "user", "content": prompt}],
            web_search=False
        )
        llm_response_content = response.choices[0].message.content
        print("LLM response received.")
    except Exception as e:
        print(f"Error during LLM inference: {e}")
        llm_response_content = f"# {today_dt.strftime('%Y年%m月%d日')} 每日電子報\n\n抱歉，由於 LLM 推論失敗，未能生成完整的電子報內容。\n錯誤訊息：{e}\n\n原始資料摘要：\n"
        for item in filtered_data:
            llm_response_content += f"- **{item['title']}**: {item['summary']}\n"


    # 5. 將生成的結果儲存成今日的電子報檔案 (YYYY-MM-DD.md)
    # 注意：雖然資料是昨日的，但電子報的生成和發送是在今日，所以檔案名稱是今日日期
    md_filename = os.path.join("eletters", f"{today_dt.isoformat()}.md")
    os.makedirs(os.path.dirname(md_filename), exist_ok=True) # 確保 eletters 目錄存在

    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(llm_response_content)
    print(f"Daily newsletter saved to: {md_filename}")

if __name__ == "__main__":
    main()
