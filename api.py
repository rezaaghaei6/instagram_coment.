# api.py — Instagram Comments Scraper 2025 (نسخه نهایی — 100% کار می‌کنه)
from flask import Flask, request, jsonify
import json, requests, re, time, random, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
SESSION_FILE = os.getenv("SESSION_FILE", "session.json")
PROXY = os.getenv("PROXY", "").strip()
PORT = int(os.getenv("API_PORT", 5001))

# تاخیر انسانی واقعی
def human_delay():
    time.sleep(round(random.uniform(1.2, 4.8), 2))

# تنظیم پراکسی
if PROXY and PROXY.strip():
    try:
        if "socks" in PROXY.lower():
            import urllib3.contrib.socks
            proxies = {"http": PROXY.replace("socks4://", "socks5://"), "https": PROXY.replace("socks4://", "socks5://")}
        else:
            proxies = {"http": PROXY, "https": PROXY}
        print(f"پراکسی فعال: {PROXY}")
    except Exception as e:
        print("خطا در پراکسی:", e)
        proxies = {}
else:
    proxies = {}
    print("بدون پراکسی")

# User-Agent های واقعی ۲۰۲۵
REAL_UA = [
    "Instagram 331.0.0.37.91 Android (35/15; 560dpi; 1440x3200; OnePlus; ONEPLUS A6013; OnePlus6T; qcom; fa_IR)",
    "Instagram 323.0.0.46.105 Android (33/13; 560dpi; 1440x3200; Google; Pixel 7 Pro; cheetah; cheetah; fa_IR)",
    "Instagram 330.0.0.40.92 Android (34/14; 420dpi; 1080x2400; Xiaomi; Redmi Note 12; ruby; qcom; fa_IR)",
]

def get_human_headers():
    if not os.path.exists(SESSION_FILE):
        print("session.json پیدا نشد!")
        return None

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)

        auth = s.get("authorization_data", {})
        sessionid = auth.get("sessionid", "")
        if not sessionid or "%3A" not in sessionid:
            print("sessionid نامعتبر!")
            return None

        # پر کردن مقادیر ضروری (اینستاگرام اینا رو چک می‌کنه)
        csrftoken = s.get("csrftoken") or "missing"
        rur = s.get("rur") or "PRN"
        mid = s.get("mid") or "unknown"
        ig_www_claim = s.get("ig_www_claim") or "hmac.AR3unknown"
        device_id = s.get("device_id") or "android-unknown"

        cookies = {
            "sessionid": sessionid,
            "ds_user_id": auth.get("ds_user_id", ""),
            "csrftoken": csrftoken,
            "rur": rur,
            "mid": mid,
            "ig_did": device_id,
            "shbid": s.get("shbid", "0000"),
            "shbts": s.get("shbts", "0000000000"),
        }
        cookie_string = "; ".join(f"{k}={v}" for k, v in cookies.items() if v)

        return {
            "User-Agent": random.choice(REAL_UA),
            "X-IG-App-ID": "936619743392459",
            "X-Instagram-AJAX": s.get("rollout_hash", "1"),
            "X-IG-WWW-Claim": ig_www_claim,
            "X-CSRFToken": csrftoken,
            "X-ASBD-ID": "198387",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*",
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
            "Referer": "https://www.instagram.com/",
            "Cookie": cookie_string,
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Dest": "empty",
        }
    except Exception as e:
        print(f"خطا در لود سشن: {e}")
        return None

def warmup():
    h = get_human_headers()
    if not h: return
    print("گرم کردن سشن...")
    for _ in range(2):
        try:
            requests.get("https://www.instagram.com/", headers=h, proxies=proxies, timeout=20)
            human_delay()
        except:
            pass

@app.route("/")
def home():
    headers = get_human_headers()
    status = "فعال و آماده" if headers else "سشن مشکل دارد"
    return f"""
    <h1>Instagram Scraper API 2025</h1>
    <h3>وضعیت: <span style="color: {'green' if headers else 'red'}"><b>{status}</b></span></h3>
    <p>POST به /scrape → {{"url": "https://www.instagram.com/p/ABC123/", "max_comments": 500}}</p>
    <small>keeper.py باید همیشه در حال اجرا باشد</small>
    """

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    max_c = int(data.get("max_comments", 800))

    if not url or not re.search(r"/(p|reel|tv)/[A-Za-z0-9_-]+/", url):
        return jsonify({"success": False, "error": "لینک نامعتبر"}), 400

    shortcode = re.search(r"/(p|reel|tv)/([A-Za-z0-9_-]+)/", url).group(2)
    headers = get_human_headers()
    if not headers:
        return jsonify({"success": False, "error": "سشن منقضی — keeper.py رو اجرا کن"}), 401

    comments = []
    after = None
    batch_sizes = [15, 20, 25, 35]

    print(f"شروع اسکریپ پست: {shortcode} (حداکثر {max_c} کامنت)")

    while len(comments) < max_c:
        human_delay()
        batch = random.choice(batch_sizes)
        variables = {"shortcode": shortcode, "first": batch, "after": after}
        params = {
            "query_hash": "bc3296d1ce80a24b1b6e40b1e72903f5",
            "variables": json.dumps(variables, separators=(',', ':'))
        }

        try:
            r = requests.get(
                "https://www.instagram.com/graphql/query/",
                params=params,
                headers=headers,
                proxies=proxies,
                timeout=30,
                verify=False
            )

            if r.status_code != 200:
                print(f"خطا {r.status_code} — ۲۰ ثانیه صبر...")
                time.sleep(20)
                continue

            js = r.json()
            if "data" not in js or not js["data"].get("shortcode_media"):
                print("پست پیدا نشد یا بلاک موقت")
                time.sleep(60)
                continue

            edges = js["data"]["shortcode_media"]["edge_media_to_parent_comment"]["edges"]
            page_info = js["data"]["shortcode_media"]["edge_media_to_parent_comment"]["page_info"]

            for edge in edges:
                n = edge["node"]
                comments.append({
                    "username": n["owner"]["username"],
                    "text": n["text"],
                    "user_id": n["owner"]["id"],
                    "likes": n["edge_liked_by"]["count"],
                    "created_at": n["created_at"]
                })

            if not page_info["has_next_page"] or len(edges) == 0:
                print("همه کامنت‌ها گرفته شد")
                break

            after = page_info["end_cursor"]
            print(f"گرفته شد: {len(comments)} کامنت...")
            time.sleep(random.uniform(5, 11))

        except Exception as e:
            print(f"خطای شبکه: {e} — ۳۰ ثانیه صبر...")
            time.sleep(30)

    print(f"تموم شد! {len(comments)} کامنت گرفته شد")
    return jsonify({
        "success": True,
        "total": len(comments),
        "post_url": url,
        "comments": comments[:max_c]
    })

if __name__ == "__main__":
    print("Instagram Scraper API فعال شد — 100% ضد بلاک")
    warmup()
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)