import requests
import json
import time
import os

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]  # ✅ Replit Secrets থেকে
API_KEY = os.environ.get("API_KEY", "demo-all-key")  # Optional

EXTERNAL_API_URL = "https://bronx-osint-website-v10.vercel.app/api/custom/telegram-scan"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Store user states
user_states = {}


# =========================
# TELEGRAM API FUNCTIONS
# =========================

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"

    # Message length check (Telegram limit: 4096 chars)
    if len(text) > 4096:
        text = text[:4090] + "..."

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        response = requests.post(url, data=payload, timeout=30)
        return response.json()
    except Exception as e:
        print("sendMessage error:", e)
        return None


def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"

    params = {"timeout": 30}

    if offset:
        params["offset"] = offset

    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except Exception as e:
        print("getUpdates error:", e)
        return {"ok": False, "result": []}


# =========================
# KEYBOARD
# =========================

def main_keyboard():
    return {
        "keyboard": [["📱 Phone Lookup"]],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


# =========================
# API CALL
# =========================

def phone_lookup(number):
    try:
        headers = {"X-API-Key": API_KEY} if API_KEY != "demo-all-key" else {}
        
        response = requests.get(
            EXTERNAL_API_URL,
            params={"number": number},
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "error",
                "message": f"API Error: {response.status_code}"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# =========================
# MESSAGE HANDLER
# =========================

def handle_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").strip()

    if text == "/start":
        user_states[user_id] = None
        send_message(
            chat_id,
            "👋 Welcome!\n\nSelect an option below.",
            main_keyboard()
        )
        return

    if text == "📱 Phone Lookup":
        user_states[user_id] = "waiting_phone"
        send_message(chat_id, "📞 Send 10 digit mobile number:")
        return

    if user_states.get(user_id) == "waiting_phone":
        if text.isdigit() and len(text) == 10:
            send_message(chat_id, "🔍 Looking up number...")

            result = phone_lookup(text)
            formatted_json = json.dumps(result, indent=4, ensure_ascii=False)

            send_message(chat_id, f"<pre>{formatted_json}</pre>")
            user_states[user_id] = None
        else:
            send_message(chat_id, "❌ Invalid input.\n\nPlease send a valid 10 digit mobile number.")
        return

    send_message(chat_id, "Please use /start and choose an option.")


# =========================
# MAIN POLLING LOOP
# =========================

def main():
    print("🤖 Bot started...")
    
    # Test API connection
    try:
        test_response = requests.get(EXTERNAL_API_URL, timeout=10)
        print(f"✅ API connected: {test_response.status_code}")
    except Exception as e:
        print(f"⚠️ API connection failed: {e}")

    offset = None

    while True:
        try:
            updates = get_updates(offset)

            if updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        handle_message(update["message"])

        except Exception as e:
            print("Main loop error:", e)

        time.sleep(1)


if __name__ == "__main__":
    main()
