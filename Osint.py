import requests
import json
import time

# =========================
# CONFIG
# =========================

BOT_TOKEN = "8946759490:AAGBH3mqTCT16SopPyA2gwaVW7ELqGZUlKM"
EXTERNAL_API_URL = "https://bronx-osint-website-v10.vercel.app/api/custom/telegram-scan?key=demo-all-key&id=7530266953"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Store user states
user_states = {}


# =========================
# TELEGRAM API FUNCTIONS
# =========================

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        requests.post(url, data=payload, timeout=30)
    except Exception as e:
        print("sendMessage error:", e)


def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"

    params = {
        "timeout": 30
    }

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
        "keyboard": [
            ["📱 Phone Lookup"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


# =========================
# DUMMY HTTPS API CALL
# =========================

def phone_lookup(number):
    """
    Educational Example

    Replace EXTERNAL_API_URL with your real API.
    """

    try:
        response = requests.get(
            EXTERNAL_API_URL,
            params={"number": number},
            timeout=30
        )

        return response.json()

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

    # /start command
    if text == "/start":
        user_states[user_id] = None

        send_message(
            chat_id,
            "👋 Welcome!\n\nSelect an option below.",
            main_keyboard()
        )
        return

    # Phone Lookup button
    if text == "📱 Phone Lookup":
        user_states[user_id] = "waiting_phone"

        send_message(
            chat_id,
            "📞 Send 10 digit mobile number:"
        )
        return

    # Waiting for phone number
    if user_states.get(user_id) == "waiting_phone":

        if text.isdigit() and len(text) == 10:

            send_message(
                chat_id,
                "🔍 Looking up number..."
            )

            result = phone_lookup(text)

            formatted_json = json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )

            send_message(
                chat_id,
                f"<pre>{formatted_json}</pre>"
            )

            user_states[user_id] = None

        else:
            send_message(
                chat_id,
                "❌ Invalid input.\n\nPlease send a valid 10 digit mobile number."
            )

        return

    # Unknown message
    send_message(
        chat_id,
        "Please use /start and choose an option."
    )


# =========================
# MAIN POLLING LOOP
# =========================

def main():
    print("Bot started...")

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
