from flask import Flask, request, jsonify
import requests
import os
import time
import json
import random
from threading import Thread

app = Flask(__name__)

# ✅ Configuration
PAGE_ACCESS_TOKEN = "EAGWp4PDBMf4BO9fRf3izdRm2OCFoQB5cL2WBUG8qLGSmVVP5AfP0xR9fgZCtPuvPc5X8z2YCk03ZC2yUYuCAeeEPZBV3Kl78RAS8FwgZAzQ8zDKTPBWV5DyX140G0mqeefFvXpxjLdf2ZAq0prNYIJhHmOIeNNZBLZBK8Ozm0tCBQMtsQksPvk1PLGurg30AZDZD"
VERIFY_TOKEN = "openofficeweb"

# ✅ Gestion des messages stockés
MESSAGES_FILE_PATH = "data.json"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

# ✅ Charger les messages en cache
try:
    if os.path.exists(MESSAGES_FILE_PATH):
        with open(MESSAGES_FILE_PATH, "r", encoding="utf-8") as f:
            messages_cache = json.load(f)
    else:
        messages_cache = {}
except Exception as e:
    print("❌ Erreur chargement messages:", e)
    messages_cache = {}

# ✅ Sauvegarde des messages dans un fichier
def save_messages():
    try:
        if os.path.exists(MESSAGES_FILE_PATH) and os.path.getsize(MESSAGES_FILE_PATH) > MAX_FILE_SIZE:
            prune_messages_cache()
        
        with open(MESSAGES_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(messages_cache, f, indent=2)
    except Exception as e:
        print("❌ Erreur sauvegarde messages:", e)

# ✅ Suppression des anciens messages si trop volumineux
def prune_messages_cache():
    if len(messages_cache) > 1000:
        oldest_key = list(messages_cache.keys())[0]
        del messages_cache[oldest_key]
        prune_messages_cache()

# ✅ Gestion des inactifs
user_last_activity = {}

# ✅ Réponses aléatoires après 1h d'inactivité
random_messages = [
    "👋 Coucou, je suis toujours en ligne ! Besoin d’aide ?",
    "🚀 Salut ! Pose-moi une question, je suis prêt à répondre.",
    "🤖 Hé ! Que puis-je faire pour toi aujourd'hui ?",
    "🔥 Toujours là si tu as besoin d’aide !",
]

# ✅ Vérification des utilisateurs inactifs
def check_user_activity():
    while True:
        now = time.time()
        inactive_users = [uid for uid in user_last_activity if now - user_last_activity[uid] > 3600]
        for uid in inactive_users:
            send_message(uid, random.choice(random_messages))
            del user_last_activity[uid]
        time.sleep(60)

# 🚀 Lancer la vérification des inactifs en arrière-plan
Thread(target=check_user_activity, daemon=True).start()

# ✅ Route principale
@app.route("/", methods=["GET"])
def home():
    return "🚀 Nano Bot fonctionne !"

# ✅ Vérification du webhook Messenger
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# ✅ Gestion des événements Messenger
@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()

    if body.get("object") == "page":
        for entry in body["entry"]:
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]

                # ✅ Gestion du bouton "Démarrer"
                if event.get("postback") and "payload" in event["postback"]:
                    handle_payload(event["postback"]["payload"], sender_id)
                    continue

                # ✅ Gestion des messages texte
                if "message" in event and "text" in event["message"]:
                    user_message = event["message"]["text"]

                    # ✅ Stockage du message dans le cache
                    message_id = event["message"].get("mid")
                    if message_id:
                        messages_cache[message_id] = {"text": user_message}
                        save_messages()

                    # ✅ Gestion d’activité
                    mark_message_as_seen(sender_id)
                    show_typing_indicator(sender_id)
                    user_last_activity[sender_id] = time.time()

                    # ✅ Réponse en arrière-plan
                    def delayed_response():
                        bot_reply = get_ai_response(user_message)
                        stop_typing_indicator(sender_id)
                        send_message(sender_id, bot_reply)

                    Thread(target=delayed_response).start()

                # ✅ Gestion des réponses aux messages
                if "message" in event and "reply_to" in event["message"]:
                    original_mid = event["message"]["reply_to"].get("mid")
                    cached_message = messages_cache.get(original_mid, {})

                    event["message"]["reply_to"]["text"] = cached_message.get("text")
                    event["message"]["reply_to"]["attachments"] = cached_message.get("attachments")

                # ✅ Gestion des réactions aux messages
                if "reaction" in event:
                    mid = event["reaction"].get("mid")
                    cached_message = messages_cache.get(mid, {})

                    event["reaction"]["text"] = cached_message.get("text")
                    event["reaction"]["attachments"] = cached_message.get("attachments")

        return "EVENT_RECEIVED", 200
    return "Not Found", 404

# ✅ Réponse IA (Chatbot)
def get_ai_response(user_message):
    try:
        prompt = f"Nano Bot est une IA avancée créée par Josué Raoult Drogba.\n\nUtilisateur: {user_message}\nNano Bot:"
        url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0..."
        response = requests.post(url, json={"prompt": prompt}, headers={"Content-Type": "application/json"}).json()

        return response.get("text", "⚠️ L'IA n'a pas pu répondre.")
    except Exception as e:
        print("❌ Erreur API:", e)
        return "⚠️ Impossible de contacter l'IA."

# ✅ Gestion du bouton "Démarrer"
def handle_payload(payload, sender_id):
    if payload == "GET_STARTED_PAYLOAD":
        send_message(sender_id, "👋 Bienvenue ! Je suis Nano Bot, une IA avancée. Comment puis-je vous aider ?")

# ✅ Envoi d'un message simple
def send_message(sender_id, text):
    message_data = {"recipient": {"id": sender_id}, "message": {"text": text}}
    send_message_to_facebook(message_data)

# ✅ Actions utilisateur (vu, écriture...)
def mark_message_as_seen(sender_id):
    send_action(sender_id, "mark_seen")

def show_typing_indicator(sender_id):
    send_action(sender_id, "typing_on")

def stop_typing_indicator(sender_id):
    send_action(sender_id, "typing_off")

def send_action(sender_id, action):
    message_data = {"recipient": {"id": sender_id}, "sender_action": action}
    send_message_to_facebook(message_data)

# ✅ Envoi du message via Messenger API
def send_message_to_facebook(message_data):
    try:
        url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        requests.post(url, json=message_data)
    except requests.exceptions.RequestException as e:
        print("Erreur d'envoi:", e)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
