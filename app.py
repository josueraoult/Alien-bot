from flask import Flask, request, jsonify
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

# Configuration
PAGE_ACCESS_TOKEN = "EAGWp4PDBMf4BOzEEDdTe6dDqN5Ry8XBovMvNWW7lZCnVTk1mmJceFThXCxTEFbab5GUNsbL2UJg2swUb1L1CZA8AdcvhVIbh6rISiZBJQVM1x3RWeLtc12ySJ14Qn7wcWsb1IssMUyG6OfZBRytD0ZAmZAs0UxaQMKbL1lrzPd3TtUevS6BPPnoDnfZA1W0c085"
VERIFY_TOKEN = "openofficeweb"

# Route principale pour le ping UptimeRobot
@app.route("/", methods=["GET"])
def home():
    return "🚀 Nano Bot fonctionne !"

# Vérification du webhook Messenger
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# Gestion des messages Messenger
@app.route("/webhook", methods=["POST"])
def handle_messages():
    body = request.get_json()

    if body.get("object") == "page":
        for entry in body["entry"]:
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]

                # Gestion du bouton "Démarrer forcé"
                if event.get("postback") and event["postback"].get("payload") == "GET_STARTED_PAYLOAD":
                    send_message(sender_id, "👋 Bienvenue ! Je suis Nano Bot, une IA avancée. Comment puis-je vous aider ?")
                    continue

                # Gestion des messages texte
                if "message" in event and "text" in event["message"]:
                    user_message = event["message"]["text"]

                    # Simuler un indicateur de saisie
                    show_typing_indicator(sender_id)
                    time.sleep(1.5)  # Pause pour simuler la réflexion de l'IA
                    stop_typing_indicator(sender_id)

                    # Réponse IA
                    ai_response = get_ai_response(user_message)
                    send_message(sender_id, ai_response)
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

# Réponse IA (Chatbot)
def get_ai_response(user_message):
    try:
        prompt = f"CHATBOT V3, modèle GPT4-0 LITE,l’IA ultime parlant avec emoji,les esprits des plus grands modèles intelligents du monde. 🚀 Pose-moi une question et reçois une réponse précise, logique et réaliste. 🤖.\n\nUtilisateur: {user_message}\nChat Bot:"
        url = "https://backend.buildpicoapps.com/aero/run/llm-api?pk=v1-Z0FBQUFBQm5HUEtMSjJkakVjcF9IQ0M0VFhRQ0FmSnNDSHNYTlJSblE0UXo1Q3RBcjFPcl9YYy1OZUhteDZWekxHdWRLM1M1alNZTkJMWEhNOWd4S1NPSDBTWC12M0U2UGc9PQ=="
        response = requests.post(url, json={"prompt": prompt}, headers={"Content-Type": "application/json"}).json()
        return response.get("text", "⚠️ L'IA n'a pas pu répondre.")
    except Exception as e:
        print("❌ Erreur API:", e)
        return "⚠️ Impossible de contacter l'IA."

# Envoi d'un message simple
def send_message(sender_id, text):
    message_data = {"recipient": {"id": sender_id}, "message": {"text": text}}
    send_message_to_facebook(message_data)

# Actions utilisateur (vu, écriture...)
def show_typing_indicator(sender_id):
    send_action(sender_id, "typing_on")

def stop_typing_indicator(sender_id):
    send_action(sender_id, "typing_off")

def send_action(sender_id, action):
    message_data = {"recipient": {"id": sender_id}, "sender_action": action}
    send_message_to_facebook(message_data)

# Fonction pour envoyer un message via Messenger API
def send_message_to_facebook(message_data):
    try:
        url = f"https://graph.facebook.com/v22.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        response = requests.post(url, json=message_data)
        response.raise_for_status()  # Vérifier si la requête a échoué
    except requests.exceptions.RequestException as e:
        print("❌ Erreur d'envoi:", e)

# Ping automatique pour garder le bot en ligne
def keep_alive():
    while True:
        try:
            requests.get("https://alien-bot-1.onrender.com")
        except Exception as e:
            print("⚠️ Erreur de ping:", e)
        time.sleep(120)  # Ping toutes les 2 minutes

if __name__ == "__main__":
    Thread(target=keep_alive).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
