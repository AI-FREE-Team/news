import json  
import os  
from datetime import datetime  
from zoneinfo import ZoneInfo  
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode  
import hashlib

TAIPEI = ZoneInfo("Asia/Taipei")  
DATA_DIR = "data"  
BATCH_PATH = "tmp/news_batch.json"

# 保留常見必要參數，其它像 utm_*, fbclid 會移除
KEEP_QUERY_KEYS = {"id", "cid", "sid", "ref"} # 可自行調整

def ensure_dirs():
  os.makedirs(DATA_DIR, exist_ok=True)  
  os.makedirs(os.path.dirname(BATCH_PATH), exist_ok=True)

def today_path(): 
  today = datetime.now(TAIPEI).date().isoformat() # YYYY-MM-DD
  return os.path.join(DATA_DIR, f"{today}.json")

def load_json(path):
  if not os.path.exists(path):
    return []
  with open(path, "r", encoding="utf-8") as f:
    try:
      return json.load(f)  
    except json.JSONDecodeError: 
      # 檔案損壞就備份並重建
      backup = path + ".corrupt"
      os.replace(path, backup)  
      return []

def save_json(path, data):  
  # 依 published_at（或 scraped_at）排序，最新在前  
  def sort_key(item):  
    return item.get("published_at") or item.get("scraped_at") or ""  
  data_sorted = sorted(data, key=sort_key, reverse=True)  
  with open(path, "w", encoding="utf-8") as f:  
    json.dump(data_sorted, f, ensure_ascii=False, indent=2)

def canonicalize_url(u: str) -> str:
  try:
    p = urlparse(u.strip())
    # 小寫網域、保留 path、移除 fragment
    netloc = p.netloc.lower()  
    path = p.path  
    # 過濾追蹤參數  
    q_pairs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)]  
    filtered = []  

    for k, v in q_pairs:
      kl = k.lower()
      if kl.startswith("utm_") or kl in {"fbclid", "gclid", "igshid", "spm"}:
        continue  
      if kl in KEEP_QUERY_KEYS:  
        filtered.append((k, v))  
    query = urlencode(filtered, doseq=True)  
    return urlunparse((p.scheme, netloc, path, "", query, ""))  
  except Exception:  
    return u.strip()

def norm_title(t: str | None) -> str:
  if not t:
    return ""  
  return " ".join(t.split()).lower()
  
def item_key(item: dict) -> str:  
  """優先用規範化 URL；沒有 URL 才退回 title 做 hash。"""  
  url = item.get("url", "")  
  title = item.get("title", "")  
  if url:  
    return "u:" + canonicalize_url(url)  
  if title:  
    return "t:" + hashlib.sha1(norm_title(title).encode("utf-8")).hexdigest()  
  # 什麼都沒有就用內容 hash（不理想，但避免 crash）  
  return "h:" + hashlib.sha1(json.dumps(item, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
  
def enrich(item: dict) -> dict:  
  out = dict(item)  
  # 填寫 scraped_at（台北時區）  
  out.setdefault("scraped_at", datetime.now(TAIPEI).isoformat(timespec="seconds"))  
  # 補 canonical_url，之後方便比對  
  if "url" in out and out["url"]:  
    out["canonical_url"] = canonicalize_url(out["url"])  
  return out

def merge_dedup(existing: list[dict], batch: list[dict]) -> list[dict]:  
  # 建 key -> item 的 map（existing 優先保留，但用 batch 覆蓋較新的欄位）  
  m = {}  
  for it in existing:  
    m[item_key(it)] = it

  for it in batch:
    e = enrich(it)
    k = item_key(e)
    if k in m:
        # 合併：保留舊值，若 batch 有提供補充欄位則覆蓋
        merged = {**m[k], **{kk: vv for kk, vv in e.items() if vv not in (None, "", [])}}
        m[k] = merged
    else:
        m[k] = e
return list(m.values())

def main():  
  ensure_dirs()
 
  # 讀本次批次
  batch = load_json(BATCH_PATH)
  if not isinstance(batch, list):
    print("Batch file should be a JSON array. Got something else; abort.")
    return
  # 讀當日累積檔
  out_path = today_path()
  existing = load_json(out_path)
  
  # 合併去重
  merged = merge_dedup(existing, batch)

  # 寫回
  save_json(out_path, merged)

  # 清空本次批次檔（可選）
  try:
    os.remove(BATCH_PATH)
  except FileNotFoundError:
    pass
  print(f"✅ Saved {len(merged)} items to {out_path}")

if __name__ == "__main__":  
  main()
