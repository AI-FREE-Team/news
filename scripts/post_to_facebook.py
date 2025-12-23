import requests
import os
import datetime

# 從環境變數獲取配置
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN')
# POST_MESSAGE 不再直接從環境變數獲取，而是從檔案讀取
# POST_MESSAGE = os.getenv('POST_MESSAGE') 

# 定義 Markdown 檔案的根目錄
# 假設你的 Markdown 檔案在 GitHub 儲存庫的根目錄下的 'eletters' 資料夾中
MARKDOWN_DIR = 'eletters' 

# 檢查必要的環境變數是否存在
if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
    print("錯誤：缺少必要的環境變數 (FB_PAGE_ID, FB_ACCESS_TOKEN)")
    exit(1)

# 1. 根據當前日期構造檔案路徑
today = datetime.date.today()
filename = today.strftime('%Y-%m-%d.md') # e.g., 2023-10-27.md
filepath = os.path.join(MARKDOWN_DIR, filename)

# 2. 讀取 Markdown 檔案內容
post_content = ""
if os.path.exists(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            post_content = f.read()
        if not post_content.strip(): # 檢查檔案是否為空
            print(f"警告：檔案 '{filepath}' 為空，將發布空白貼文或根據 Facebook API 規則處理。")
    except Exception as e:
        print(f"錯誤：讀取檔案 '{filepath}' 時發生問題: {e}")
        exit(1)
else:
    print(f"錯誤：找不到當天日期的 Markdown 檔案 '{filepath}'。請確保檔案存在。")
    exit(1)

# 如果讀取到內容，則使用它；否則，如果設計上不允許空貼文，可以在此處設置一個默認值或報錯
if not post_content:
    print("錯誤：無法獲取貼文內容。檔案可能不存在或為空。")
    exit(1)


url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"

import re

def optimize_md_for_fb(text):
    """
    將 Markdown 格式轉換為適合 Facebook 發文的格式
    利用 Unicode 字符模擬粗體、斜體，並優化結構。
    """
    
    # --- Unicode 轉換表 ---
    def to_unicode_variant(text, style="bold"):
        # 這是簡單的對應表，處理 A-Z, a-z, 0-9
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        
        # 粗體 (Mathematical Bold)
        bold_chars = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏Ｑ𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
        # 斜體 (Mathematical Italic)
        italic_chars = "𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧0123456789"
        # 刪除線
        strikethrough_char = "\u0336"

        if style == "bold":
            trans = str.maketrans(chars, bold_chars)
            return text.translate(trans)
        elif style == "italic":
            trans = str.maketrans(chars, italic_chars)
            return text.translate(trans)
        elif style == "strike":
            return "".join([c + strikethrough_char for c in text])
        return text

    # 1. 處理標題 (Header) - FB 不支援大字體，所以用粗體 + Emoji 裝飾
    def replace_header(match):
        level = len(match.group(1)) # # 的數量
        content = match.group(2).upper() # 標題通常大寫較顯眼
        icons = {1: "📢", 2: "📌", 3: "🔹"}
        icon = icons.get(level, "▪️")
        return f"\n{icon} {to_unicode_variant(content, 'bold')}\n"

    text = re.sub(r'^(#+)\s+(.*)', replace_header, text, flags=re.MULTILINE)

    # 2. 處理粗體 (**text**)
    text = re.sub(r'\*\*(.*?)\*\*', lambda m: to_unicode_variant(m.group(1), "bold"), text)

    # 3. 處理斜體 (*text*)
    text = re.sub(r'\*(.*?)\*', lambda m: to_unicode_variant(m.group(1), "italic"), text)

    # 4. 處理刪除線 (~~text~~)
    text = re.sub(r'~~(.*?)~~', lambda m: to_unicode_variant(m.group(1), "strike"), text)

    # 5. 處理清單 (List) - 將 - 或 * 換成更漂亮的點
    text = re.sub(r'^\s*[\-\*]\s+', "✅ ", text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', "➔ ", text, flags=re.MULTILINE)

    # 6. 處理連結 ([text](url)) - FB 會自動抓 Link Preview，但文字格式需調整
    # 如果想保留文字，格式改為: 文字 (url)
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1: \2', text)

    # 7. 清理多餘空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

params = {
    'message': optimize_md_for_fb(post_content), # 使用從檔案讀取的內容
    'access_token': FB_ACCESS_TOKEN
}

print(f"準備發布貼文到 Facebook 粉絲專頁 ID: {FB_PAGE_ID}")
print(f"從檔案 '{filepath}' 讀取的貼文內容前100字: {post_content[:100]}...") # 只顯示前100字預覽

try:
    # 發送 POST 請求
    response = requests.post(url, data=params)

    # 輸出完整的 HTTP 回應（包含 headers 和 body）
    print("\n--- Facebook API 回應 ---")
    print("Status Code:", response.status_code)
    print("Response Headers:")
    for key, value in response.headers.items():
        print(f"{key}: {value}")
    print("\nResponse Body:")
    print(response.text)

    # 檢查回應狀態碼
    if response.status_code == 200:
        print("\nFacebook 貼文發布成功！")
    else:
        print(f"\nFacebook 貼文發布失敗，狀態碼: {response.status_code}")
        print(f"錯誤訊息: {response.text}")
        exit(1) # 如果失敗，讓 GitHub Action 報錯
        
except requests.exceptions.RequestException as e:
    print(f"發送請求時發生錯誤: {e}")

    exit(1) # 如果請求失敗，讓 GitHub Action 報錯
