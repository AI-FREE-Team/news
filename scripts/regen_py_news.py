import json
import os
import sys
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def regenerate_newsletter(custom_prompt=None):
    """
    重新生成今日的電子報
    
    Args:
        custom_prompt: 使用者自訂的額外提示詞，會附加到原有 prompt 之後
    """
    # 1. 計算昨日和今日日期
    today_dt = datetime.now(TAIPEI).date() - timedelta(days=1)
    yesterday_dt = today_dt - timedelta(days=1)
    yesterday_iso = yesterday_dt.isoformat()
    today_iso = today_dt.isoformat()

    print(f"Regenerating newsletter for {today_iso} using data from {yesterday_iso}")
    if custom_prompt:
        print(f"Custom prompt received: {custom_prompt}")

    # 2. 讀取 data/ 資料夾中的昨日 JSON 檔案
    data_dir = "data"
    yesterday_data_path = os.path.join(data_dir, f"{yesterday_iso}.json")
    print(f"Loading data from: {yesterday_data_path}")
    articles = load_json(yesterday_data_path)

    if not articles:
        print("No articles found for yesterday. Creating empty newsletter.")
        md_filename = os.path.join("eletters", f"{today_iso}.md")
        os.makedirs(os.path.dirname(md_filename), exist_ok=True)
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(f"# {today_dt.strftime('%Y年%m月%d日')} 每日電子報\n\n")
            f.write("抱歉，沒有找到昨日的文章資料來生成電子報。\n")
        return

    # 3. 只抓取 'title' 和 'summary'
    filtered_data = []
    for article in articles:
        if 'title' in article and 'summary' in article:
            filtered_data.append({
                "title": article["title"],
                "summary": article["summary"]
            })
    
    if not filtered_data:
        print("No valid title or summary found. Creating empty newsletter.")
        md_filename = os.path.join("eletters", f"{today_iso}.md")
        os.makedirs(os.path.dirname(md_filename), exist_ok=True)
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(f"# {today_dt.strftime('%Y年%m月%d日')} 每日電子報\n\n")
            f.write("抱歉，昨日的文章資料中沒有找到有效的標題或摘要。\n")
        return

    # 4. 準備給 LLM 的 prompt（與原版相同的基礎 prompt）
    prompt_parts = [
        f"你是一個專業的 AI 產業專家，經營一個專業的粉絲社群，粉絲社群名稱叫做 AI . FREE News，"
        f"依據最新的AI重點新聞進行綜合整理跟分析，每天會去撰寫分享AI趨勢洞察。"
        f"請根據以下內容，生成一份關於 {yesterday_dt.strftime('%Y年%m月%d日')} 的每日 AI 趨勢洞察分析，"
        f"在文末請用幾句話總結趨勢並鼓勵讀者繼續跟 AI . FREE Team 繼續探索AI的世界。"
    ]
    
    for i, item in enumerate(filtered_data):
        prompt_parts.append(f"\n## 文章 {i+1}: {item['title']}")
        prompt_parts.append(f"摘要: {item['summary']}")
    
    # 5. 如果有自訂 prompt，附加到後面
    if custom_prompt and custom_prompt.strip():
        prompt_parts.append(f"\n\n## 額外需求：\n{custom_prompt}")
    
    prompt_parts.append("\n請以 Markdown 格式，內容可加入Emoji。")
    prompt = "\n".join(prompt_parts)

    print("Sending prompt to LLM for regeneration...")
    
    # 6. 透過 g4f 進行推論
    try:
        client = Client()
        response = client.chat.completions.create(
            model="gemma-3-27b-it",
            messages=[{"role": "user", "content": prompt}],
            web_search=False
        )
        llm_response_content = response.choices[0].message.content
        print("LLM response received successfully.")
    except Exception as e:
        print(f"Error during LLM inference: {e}")
        llm_response_content = (
            f"# {today_dt.strftime('%Y年%m月%d日')} 每日電子報\n\n"
            f"抱歉，由於 LLM 推論失敗，未能生成完整的電子報內容。\n"
            f"錯誤訊息：{e}\n\n原始資料摘要：\n"
        )
        for item in filtered_data:
            llm_response_content += f"- **{item['title']}**: {item['summary']}\n"

    # 7. 將生成的結果儲存（覆蓋今日的電子報檔案）
    md_filename = os.path.join("eletters", f"{today_iso}.md")
    os.makedirs(os.path.dirname(md_filename), exist_ok=True)

    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(llm_response_content)
    
    print(f"Newsletter regenerated and saved to: {md_filename}")
    print("✅ Regeneration completed successfully!")

def main():
    # 從命令列參數讀取自訂 prompt（如果有的話）
    custom_prompt = None
    if len(sys.argv) > 1:
        custom_prompt = sys.argv[1]
    
    regenerate_newsletter(custom_prompt)

if __name__ == "__main__":
    main()
