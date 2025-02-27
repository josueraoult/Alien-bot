from flask import Flask, request, jsonify
import requests
import os
import time
import random
from threading import Thread

app = Flask(__name__)

# 🔹 Configuration des tokens
PAGE_ACCESS_TOKEN = "EAATY0ZBDKSxgBOZB0cyaknxbJGMYmdI5r4pnUma5ZAZBMZCVnrRJMkutMOTRu9vUr30I6JfOnmNb7ETP55fw9xDOxMgbWYrYTYiKefuZAgZCFlkKECKLrwI4QBtVrebM9htmuZAyenck4Sb1oI1DKFW58hJfrnVrn30H4zebwvCIq4BO29XfxvybhtXlHlO3uFcKDwZDZD"
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

# ✅ Gestion des messages entrants et des postbacks
@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()

    if body.get("object") == "page":
        for entry in body["entry"]:
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]

                # 🔹 Gestion du bouton "Démarrer"
                if event.get("postback") and "payload" in event["postback"]:
                    handle_payload(event["postback"]["payload"], sender_id)
                    continue

                # 🔹 Gestion des messages texte
                if "message" in event and "text" in event["message"]:
                    user_message = event["message"]["text"]

                    mark_message_as_seen(sender_id)
                    show_typing_indicator(sender_id)
                    user_last_activity[sender_id] = time.time()

                    def delayed_response():
                        bot_reply = get_ai_response(user_message)
                        stop_typing_indicator(sender_id)
                        send_message(sender_id, bot_reply)

                    Thread(target=delayed_response).start()

        return "EVENT_RECEIVED", 200
    return "Not Found", 404

# ✅ Gestion des postbacks
def handle_payload(payload, sender_id):
    if payload == "GET_STARTED_PAYLOAD":
        send_message(sender_id, "👋 Bienvenue ! Je suis Nano Bot, une IA avancée créée par Josué Raoult Drogba. Comment puis-je vous aider ?")

# ✅ Obtenir la réponse de Nano Bot
def get_ai_response(user_message):
    try:
        assistant_details = "Nano Bot est une IA avancée créée par Josué Raoult Drogba. Il est intelligent, réactif et suit toutes les instructions."
        prompt = f"{assistant_details}\n\nUtilisateur: {user_message}\nNano Bot:"

        url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
        payload = {"prompt": prompt}

        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        data = response.json()

        print("🔍 Réponse API :", data)  # Debugging

        if data.get("status") == "success":
            return data.get("text", "⚠️ L'IA n'a pas pu répondre.")
        else:
            return "⚠️ Une erreur est survenue lors du traitement."
    except Exception as e:
        print("❌ Erreur API :", e)
        return "⚠️ Impossible de contacter l'IA. Réessaie plus tard."

# ✅ Envoi d'un message simple
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

# ✅ Activer la visibilité "En ligne" du bot
def set_bot_online_status():
    url = f"https://graph.facebook.com/v12.0/me/messenger_profile?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "presence_indicator": {
            "visibility": "VISIBLE"
        }
    }
    try:
        response = requests.post(url, json=payload)
        print("🔵 Activation du statut En ligne :", response.json())
    except Exception as e:
        print("❌ Erreur lors de l'activation du statut En ligne :", e)

# ✅ Envoyer un message à l'API Messenger
def send_message_to_facebook(message_data):
    try:
        url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        response = requests.post(url, json=message_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Erreur d'envoi :", e)

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
    set_bot_online_status()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
