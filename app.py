from flask import Flask, request, jsonify
import requests
import os
import time
import random
from threading import Thread

app = Flask(__name__)

# 🔹 Configuration des tokens
PAGE_ACCESS_TOKEN = "EAATY0ZBDKSxg..."
VERIFY_TOKEN = "openofficeweb"

# 🔹 Messages aléatoires après 1h d'inactivité
random_messages = [
    "👋 Coucou, je suis toujours en ligne ! Besoin d’aide ?",
    "🚀 Salut ! Pose-moi une question, je suis prêt à répondre.",
    "🤖 Hé ! Que puis-je faire pour toi aujourd'hui ?",
    "🔥 Toujours là si tu as besoin d’aide !",
]

# 🔹 Stocker l'activité récente des utilisateurs
user_last_activity = {}

# ✅ Route principale
@app.route("/", methods=["GET"])
def home():
    return "🚀 Alien Bot AI fonctionne ! Le serveur est en ligne."

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
                    send_main_menu(sender_id)
                    continue

                # 🔹 Gestion des boutons
                if event.get("postback"):
                    payload = event["postback"]["payload"]
                    handle_button_click(sender_id, payload)
                    continue

                # 🔹 Gestion des messages texte
                if "message" in event and "text" in event["message"]:
                    user_message = event["message"]["text"].strip().lower()
                    user_last_activity[sender_id] = time.time()

                    if user_message == "home":
                        send_main_menu(sender_id)
                    else:
                        process_user_message(sender_id, user_message)

        return "EVENT_RECEIVED", 200
    return "Not Found", 404

# ✅ Menu principal
def send_main_menu(sender_id):
    message_data = {
        "recipient": {"id": sender_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "👽 Bienvenue sur Alien Bot ! Choisissez une fonctionnalité :",
                    "buttons": [
                        {"type": "postback", "title": "📸 Bannière FB", "payload": "BANNER"},
                        {"type": "postback", "title": "🎨 Image IA", "payload": "IMAGE_IA"},
                        {"type": "postback", "title": "🎵 Trouver une musique", "payload": "FIND_SONG"},
                        {"type": "postback", "title": "🤖 Chat IA", "payload": "CHAT_IA"},
                    ]
                }
            }
        }
    }
    send_message_to_facebook(message_data)

# ✅ Gestion des boutons
def handle_button_click(sender_id, payload):
    if payload == "BANNER":
        send_banner_image(sender_id)
    elif payload == "IMAGE_IA":
        send_ai_image(sender_id, "alien")
    elif payload == "FIND_SONG":
        send_find_song(sender_id, "if a angel has flown away from me")
    elif payload == "CHAT_IA":
        send_message(sender_id, "💬 Envoie-moi un message et je te répondrai avec l'IA !")

# ✅ Gestion des messages utilisateur
def process_user_message(sender_id, message):
    if message.startswith("bannière"):
        send_banner_image(sender_id)
    elif message.startswith("image ia"):
        send_ai_image(sender_id, message.replace("image ia ", ""))
    elif message.startswith("trouver musique"):
        send_find_song(sender_id, message.replace("trouver musique ", ""))
    elif message.startswith("chat ia"):
        get_ai_response(sender_id, message)
    else:
        send_message(sender_id, "❌ Désolé, je n'ai pas compris. Utilise les boutons ou envoie 'home' pour revenir au menu.")

# ✅ Génération de bannière FB
def send_banner_image(sender_id):
    url = "https://api.zetsu.xyz/canvas/fbcover?name=Alien&subname=Bot&sdt=n/a&address=Galaxy&email=alien@bot.com&uid=1&color=Green"
    send_message(sender_id, f"📸 Voici ta bannière : {url}")

# ✅ Génération d’image IA
def send_ai_image(sender_id, prompt):
    url = f"https://api.zetsu.xyz/api/flux?prompt={prompt}&model=4"
    send_message(sender_id, f"🎨 Voici ton image IA : {url}")

# ✅ Recherche de musique
def send_find_song(sender_id, lyrics):
    url = f"https://api.zetsu.xyz/api/findsong?lyrics={lyrics}"
    send_message(sender_id, f"🎵 Voici la chanson trouvée : {url}")

# ✅ Chat IA
def get_ai_response(sender_id, message):
    try:
        url = f"https://api.zetsu.xyz/gemini?prompt={message}"
        response = requests.get(url)
        data = response.json()
        reply = data.get("gemini", "⚠️ L'IA n'a pas pu répondre.")
        send_message(sender_id, reply)
    except Exception as e:
        send_message(sender_id, "⚠️ Impossible de contacter l'IA.")

# ✅ Envoi d’un message simple
def send_message(sender_id, text):
    message_data = {"recipient": {"id": sender_id}, "message": {"text": text}}
    send_message_to_facebook(message_data)

# ✅ Vérification des utilisateurs inactifs
def check_user_activity():
    while True:
        now = time.time()
        for user_id in list(user_last_activity.keys()):
            if now - user_last_activity[user_id] > 60:  # 1 min d'inactivité
                send_main_menu(user_id)
                del user_last_activity[user_id]
        time.sleep(30)

# ✅ Envoi d’un message à l’API Messenger
def send_message_to_facebook(message_data):
    try:
        url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        response = requests.post(url, json=message_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Erreur d'envoi :", e)

# 🚀 Lancer la vérification des utilisateurs inactifs en arrière-plan
Thread(target=check_user_activity, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
