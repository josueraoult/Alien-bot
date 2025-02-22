from flask import Flask, request, jsonify
import requests
import os
import time
import threading
import random

app = Flask(__name__)

# 🚀 Ton token d'accès à la page Facebook
PAGE_ACCESS_TOKEN = "EAATY0ZBDKSxgBO8tpNKrZBZAwqxa8GPyJmJaXuA5p4V7zkDWTMwN6jRMyPlnJSqoz6Vjn6qJJM8H4B5UCgWOUd9v4ODRuETjoPzugJHspq88JDfsjwNfGNyfwTP6BmllnZC0xPhr8gHocidFHXenL7z3E8boLSN8t9qhljyEP7U3x2kqIMljmtIBShZA82pdf70cRvH8eNwZDZD"
VERIFY_TOKEN = "openofficeweb"

randomMessages = [
    "👋 Coucou, je suis toujours en ligne ! Besoin d’aide ?",
    "🚀 Salut ! Pose-moi une question, je suis prêt à répondre.",
    "🤖 Hé ! Que puis-je faire pour toi aujourd'hui ?",
    "🔥 Toujours là si tu as besoin d’aide !",
]

userLastActivity = {}

# 🚀 Route principale
@app.route("/", methods=["GET"])
def home():
    return "🚀 Alien Bot AI fonctionne ! Le serveur est en ligne."

# 🔹 Vérification du webhook Messenger
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# 🔹 Gestion des messages et événements Messenger
@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()

    if body.get("object") == "page":
        for entry in body["entry"]:
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]

                # 🔥 Détection du bouton "Démarrer"
                if event.get("postback") and event["postback"].get("payload") == "GET_STARTED":
                    send_welcome_message(sender_id)
                    continue  # On passe à l'itération suivante

                # 🔥 Si l'utilisateur envoie un message texte
                if "message" in event and "text" in event["message"]:
                    user_message = event["message"]["text"]

                    mark_message_as_seen(sender_id)
                    show_typing_indicator(sender_id)
                    userLastActivity[sender_id] = time.time()

                    def delayed_response():
                        bot_reply = get_ai_response(user_message)
                        stop_typing_indicator(sender_id)
                        send_message(sender_id, bot_reply)

                    threading.Thread(target=delayed_response).start()

        return "EVENT_RECEIVED", 200
    return "Not Found", 404

# 🔹 Envoie du message de bienvenue
def send_welcome_message(sender_id):
    send_message(sender_id, "👋 Bienvenue sur Alien Bot AI ! Comment puis-je vous aider ?")

# 🔹 Obtenir une réponse de l'IA (avec vérification des erreurs)
def get_ai_response(user_message):
    try:
        response = requests.get(f"https://api.zetsu.xyz/gemini?prompt={user_message}")
        data = response.json()
        return data.get("message", "Je n'ai pas compris. Peux-tu reformuler ?")
    except Exception as e:
        print("Erreur API :", e)
        return "Erreur de connexion avec l'API."

# 🔹 Envoie un message à l'utilisateur
def send_message(sender_id, text):
    message_data = {
        "recipient": {"id": sender_id},
        "message": {"text": text},
    }
    send_message_to_facebook(message_data)

# 🔹 Marquer un message comme "vu"
def mark_message_as_seen(sender_id):
    message_data = {"recipient": {"id": sender_id}, "sender_action": "mark_seen"}
    send_message_to_facebook(message_data)

# 🔹 Afficher "En train d'écrire..."
def show_typing_indicator(sender_id):
    message_data = {"recipient": {"id": sender_id}, "sender_action": "typing_on"}
    send_message_to_facebook(message_data)

# 🔹 Désactiver "En train d'écrire..."
def stop_typing_indicator(sender_id):
    message_data = {"recipient": {"id": sender_id}, "sender_action": "typing_off"}
    send_message_to_facebook(message_data)

# 🔹 Envoi de message à Facebook
def send_message_to_facebook(message_data):
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    try:
        response = requests.post(url, json=message_data)
        response.raise_for_status()
    except Exception as e:
        print("Erreur d'envoi :", e)

# 🔹 Activer le bouton "Démarrer"
def setup_get_started_button():
    url = f"https://graph.facebook.com/v12.0/me/messenger_profile?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "get_started": {"payload": "GET_STARTED"}
    }
    try:
        response = requests.post(url, json=payload)
        print("Configuration du bouton Démarrer:", response.json())
    except Exception as e:
        print("Erreur de configuration :", e)

# 🔹 Vérification toutes les heures pour envoyer un message automatique
def check_user_activity():
    while True:
        now = time.time()
        for user_id in list(userLastActivity.keys()):
            if now - userLastActivity[user_id] > 3600:
                send_message(user_id, random.choice(randomMessages))
                del userLastActivity[user_id]
        time.sleep(60)

# 🚀 Lancer les tâches en arrière-plan
threading.Thread(target=check_user_activity, daemon=True).start()

if __name__ == "__main__":
    setup_get_started_button()  # Active le bouton "Démarrer"
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
