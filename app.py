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

# ✅ Fonction pour envoyer un message avec des boutons
def send_button_message(sender_id):
    message_data = {
        "recipient": {"id": sender_id},
        "message": {
            "text": "Here are your options:",
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "Check Profile",
                    "payload": "CHECK_PROFILE_PAYLOAD",
                },
                {
                    "content_type": "text",
                    "title": "Say Hello",
                    "payload": "HELLO_PAYLOAD",
                },
            ],
        },
    }
    send_message_to_facebook(message_data)

# ✅ Envoi du message via Messenger API
def send_message_to_facebook(message_data):
    try:
        url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        response = requests.post(url, json=message_data)
        response.raise_for_status()  # Raise an error if the request failed
    except requests.exceptions.RequestException as e:
        print("❌ Erreur d'envoi:", e)

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

                    # ✅ Envoi d'un message avec des boutons si le message est "show buttons"
                    if user_message.lower() == "show buttons":
                        send_button_message(sender_id)
                        continue

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
    elif payload == "HELLO_PAYLOAD":
        send_message(sender_id, "👋 Hello! Comment puis-je vous assister aujourd'hui ?")
    elif payload == "CHECK_PROFILE_PAYLOAD":
        send_message(sender_id, "Voici mon profil: https://www.facebook.com/yandeva.me")

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
