from flask import Flask, request, jsonify
import requests
import os
import time
import random
from threading import Thread

app = Flask(__name__)

# 🔹 Configuration des tokens
PAGE_ACCESS_TOKEN = "TON_ACCESS_TOKEN_ICI"
VERIFY_TOKEN = "TON_VERIFY_TOKEN_ICI"

# 🔹 Messages aléatoires
random_messages = [
    "👋 Coucou, je suis toujours en ligne ! Besoin d’aide ?",
    "🚀 Salut ! Pose-moi une question, je suis prêt à répondre.",
    "🤖 Hé ! Que puis-je faire pour toi aujourd’hui ?",
    "🔥 Toujours là si tu as besoin d’aide !",
]

# 🔹 Stocker l’activité récente des utilisateurs
user_last_activity = {}

# ✅ Route principale
@app.route("/", methods=["GET"])
def home():
    return "🚀 Alien Bot AI fonctionne !"

# ✅ Vérification du webhook pour Messenger
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# ✅ Gestion des messages entrants
@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()

    if body.get("object") == "page":
        for entry in body["entry"]:
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]

                # 🔹 Détection du bouton "Démarrer"
                if event.get("postback") and event["postback"].get("payload") == "GET_STARTED":
                    send_welcome_message(sender_id)
                    continue

                # 🔹 Si l’utilisateur envoie un message texte
                if "message" in event and "text" in event["message"]:
                    user_message = event["message"]["text"]

                    mark_message_as_seen(sender_id)
                    show_typing_indicator(sender_id)
                    user_last_activity[sender_id] = time.time()

                    # Réponse différée
                    def delayed_response():
                        bot_reply = get_ai_response(user_message)
                        stop_typing_indicator(sender_id)
                        send_message(sender_id, bot_reply)

                    Thread(target=delayed_response).start()

        return "EVENT_RECEIVED", 200
    return "Not Found", 404

# ✅ Message de bienvenue avec image
def send_welcome_message(sender_id):
    message_data = {
        "recipient": {"id": sender_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {
                    "url": "https://imgur.com/a/NHgkX4N",
                    "is_reusable": True
                }
            }
        }
    }
    send_message_to_facebook(message_data)

    text_message = {
        "recipient": {"id": sender_id},
        "message": {"text": "👋 Bienvenue sur Alien Bot AI ! Comment puis-je vous aider ?"}
    }
    send_message_to_facebook(text_message)

# ✅ Envoi d’un message simple
def send_message(sender_id, text):
    message_data = {
        "recipient": {"id": sender_id},
        "message": {"text": text},
    }
    send_message_to_facebook(message_data)

# ✅ Message automatique après inactivité
def send_online_status_message(sender_id):
    random_msg = random.choice(random_messages)
    send_message(sender_id, random_msg)

# ✅ Actions utilisateur (vu, écriture…)
def mark_message_as_seen(sender_id):
    send_action(sender_id, "mark_seen")

def show_typing_indicator(sender_id):
    send_action(sender_id, "typing_on")

def stop_typing_indicator(sender_id):
    send_action(sender_id, "typing_off")

def send_action(sender_id, action):
    message_data = {"recipient": {"id": sender_id}, "sender_action": action}
    send_message_to_facebook(message_data)

# ✅ Envoyer un message à l’API Messenger
def send_message_to_facebook(message_data):
    try:
        url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        response = requests.post(url, json=message_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Erreur d’envoi :", e)

# ✅ Activer le bouton "Démarrer" et le menu persistant avec image
def setup_messenger_profile():
    url = f"https://graph.facebook.com/v12.0/me/messenger_profile?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "get_started": {"payload": "GET_STARTED"},
        "persistent_menu": [
            {
                "locale": "default",
                "composer_input_disabled": False,
                "call_to_actions": [
                    {
                        "type": "web_url",
                        "title": "💼 My Boss",
                        "url": "https://www.facebook.com/profile.php?id=61573695652333",
                        "webview_height_ratio": "full"
                    },
                    {
                        "type": "postback",
                        "title": "📷 Voir l’image",
                        "payload": "VIEW_IMAGE"
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(url, json=payload)
        print("Configuration Messenger :", response.json())
    except Exception as e:
        print("Erreur de configuration :", e)

# ✅ Vérification des utilisateurs inactifs
def check_user_activity():
    while True:
        now = time.time()
        inactive_users = [user_id for user_id in user_last_activity if now - user_last_activity[user_id] > 3600]

        for user_id in inactive_users:
            send_online_status_message(user_id)
            del user_last_activity[user_id]

        time.sleep(60)

# 🚀 Lancer les tâches en arrière-plan
Thread(target=check_user_activity, daemon=True).start()

if __name__ == "__main__":
    setup_messenger_profile()  # Active le bouton "Démarrer" et le menu
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
