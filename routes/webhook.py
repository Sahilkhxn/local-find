from flask import Blueprint, request, jsonify
import requests as http
import os

webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

TOKEN    = os.getenv('WHATSAPP_TOKEN', '')
PHONE_ID = os.getenv('PHONE_NUMBER_ID', '')
VERIFY   = os.getenv('VERIFY_TOKEN', 'localfind_secret')

sessions = {}

def send_text(to, text):
    http.post(
        f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    )

def flow(phone, msg):
    s = sessions.get(phone, {"step": "start"})
    msg = msg.strip().lower()

    if s["step"] == "start" or msg in ["hi", "hello", "start"]:
        sessions[phone] = {"step": "menu"}
        send_text(phone, "🙏 *LocalFind Jaipur* mein swagat!\n\nKya chahiye?\n1️⃣ Shop Dhundna\n2️⃣ Item Order\n3️⃣ Help\n\n_Number bhejein (1, 2, ya 3)_")

    elif msg == "1":
        sessions[phone] = {"step": "find_query"}
        send_text(phone, "🔍 Kya dhundna hai? Likhein:\n_(e.g. doodh, hardware, kapde)_")

    elif s["step"] == "find_query":
        from db.schema import get_db
        db = get_db()
        rows = db.execute(
            "SELECT shop_name, address, wa_primary FROM shops WHERE is_active=1 AND (category LIKE ? OR description LIKE ?) LIMIT 5",
            (f"%{msg}%", f"%{msg}%")
        ).fetchall()
        db.close()
        if rows:
            reply = f"✅ *'{msg}'* ke liye {len(rows)} shop mili:\n\n"
            for i, r in enumerate(rows, 1):
                reply += f"{i}. *{r['shop_name']}*\n📍 {r['address']}\n📞 {r['wa_primary']}\n\n"
        else:
            reply = f"😕 *'{msg}'* ke liye koi shop nahi mili."
        send_text(phone, reply)
        sessions[phone] = {"step": "start"}

    elif msg == "2":
        sessions[phone] = {"step": "order_name"}
        send_text(phone, "✍️ Aapka *naam* batayein:")

    elif s["step"] == "order_name":
        s["name"] = msg
        s["step"] = "order_item"
        sessions[phone] = s
        send_text(phone, f"👋 Hello *{msg}*! Kaunsa *item* chahiye?")

    elif s["step"] == "order_item":
        s["item"] = msg
        s["step"] = "order_address"
        sessions[phone] = s
        send_text(phone, "📍 Apna *area/address* batayein:")

    elif s["step"] == "order_address":
        from db.schema import get_db
        db = get_db()
        db.execute(
            "INSERT INTO wa_bookings (phone, name, item, address) VALUES (?,?,?,?)",
            (phone, s.get("name"), s.get("item"), msg)
        )
        db.commit()
        db.close()
        send_text(phone,
            f"✅ *Order Saved!*\n\n"
            f"👤 {s.get('name')}\n"
            f"🛒 {s.get('item')}\n"
            f"📍 {msg}\n\n"
            f"Hum jald connect karenge! 🙏"
        )
        sessions[phone] = {"step": "start"}

    elif msg == "3":
        send_text(phone, "ℹ️ *LocalFind Jaipur*\n\nShop dhundein ya order karein!\nSite: https://yoursite.com\n\n_'Hi' likhein menu ke liye_ 😊")
        sessions[phone] = {"step": "start"}

    else:
        send_text(phone, "😊 *1, 2, ya 3* likhein menu ke liye!")
        sessions[phone] = {"step": "start"}

# ── Meta Webhook Verify (GET) ──
@webhook_bp.route('/whatsapp', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY:
        return request.args.get('hub.challenge'), 200
    return 'Forbidden', 403

# ── Incoming Messages (POST) ──
@webhook_bp.route('/whatsapp', methods=['POST'])
def webhook():
    print("POST AAYA!", flush=True)  # ← YE ADD KARO
    print(request.get_json(), flush=True)
    try:
        entry = request.get_json()['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            m     = entry['messages'][0]
            phone = m['from']
            text  = m['text']['body'] if m['type'] == 'text' else ''
            if text:
                flow(phone, text)
    except Exception as e:
        print(f"WA Error: {e}")
    return jsonify({'status': 'ok'}), 200