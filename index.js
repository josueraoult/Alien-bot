const express = require("express");
const bodyParser = require("body-parser");
const axios = require("axios");
require("dotenv").config();

const app = express();
app.use(bodyParser.json());

const PAGE_ACCESS_TOKEN = "EAATY0ZBDKSxgBO8tpNKrZBZAwqxa8GPyJmJaXuA5p4V7zkDWTMwN6jRMyPlnJSqoz6Vjn6qJJM8H4B5UCgWOUd9v4ODRuETjoPzugJHspq88JDfsjwNfGNyfwTP6BmllnZC0xPhr8gHocidFHXenL7z3E8boLSN8t9qhljyEP7U3x2kqIMljmtIBShZA82pdf70cRvH8eNwZDZD";
const VERIFY_TOKEN = "openofficeweb";

const randomMessages = [
    "👋 Coucou, je suis toujours en ligne ! Besoin d’aide ?",
    "🚀 Salut ! Pose-moi une question, je suis prêt à répondre.",
    "🤖 Hé ! Que puis-je faire pour toi aujourd'hui ?",
    "🔥 Toujours là si tu as besoin d’aide !",
];

let userLastActivity = {}; 

// 🚀 Correction: Route pour la racine (évite "Cannot GET /")
app.get("/", (req, res) => {
    res.send("🚀 Alien Bot AI fonctionne ! Le serveur est en ligne.");
});

// Vérification du webhook
app.get("/", (req, res) => {
    let mode = req.query["hub.mode"];
    let token = req.query["hub.verify_token"];
    let challenge = req.query["hub.challenge"];

    if (mode === "subscribe" && token === VERIFY_TOKEN) {
        res.status(200).send(challenge);
    } else {
        res.sendStatus(403);
    }
});

// Gestion des messages entrants
app.post("/webhook", async (req, res) => {
    let body = req.body;

    if (body.object === "page") {
        body.entry.forEach(async (entry) => {
            let event = entry.messaging[0];
            let senderId = event.sender.id;

            if (event.message && event.message.text) {
                let userMessage = event.message.text;

                markMessageAsSeen(senderId);
                showTypingIndicator(senderId);
                userLastActivity[senderId] = Date.now();

                setTimeout(async () => {
                    let botReply = await getAIResponse(userMessage);
                    stopTypingIndicator(senderId);
                    sendMessage(senderId, botReply);
                }, 2000);
            }
        });

        res.status(200).send("EVENT_RECEIVED");
    } else {
        res.sendStatus(404);
    }
});

function sendWelcomeMessage(senderId) {
    let messageData = {
        recipient: { id: senderId },
        message: { text: "Bienvenue sur Alien Bot AI ! Comment puis-je vous aider ?" },
    };
    sendMessageToFacebook(messageData);
}

async function getAIResponse(userMessage) {
    try {
        let response = await axios.get(`https://api.zetsu.xyz/gemini?prompt=${encodeURIComponent(userMessage)}`);
        return response.data.message || "Je n'ai pas compris. Peux-tu reformuler ?";
    } catch (error) {
        console.error("Erreur API :", error);
        return "Une erreur est survenue, réessaie plus tard.";
    }
}

function sendMessage(senderId, text) {
    let messageData = {
        recipient: { id: senderId },
        message: { text },
    };
    sendMessageToFacebook(messageData);
}

function sendOnlineStatusMessage(senderId) {
    let randomMsg = randomMessages[Math.floor(Math.random() * randomMessages.length)];
    sendMessage(senderId, randomMsg);
}

function markMessageAsSeen(senderId) {
    let messageData = {
        recipient: { id: senderId },
        sender_action: "mark_seen",
    };
    sendMessageToFacebook(messageData);
}

function showTypingIndicator(senderId) {
    let messageData = {
        recipient: { id: senderId },
        sender_action: "typing_on",
    };
    sendMessageToFacebook(messageData);
}

function stopTypingIndicator(senderId) {
    let messageData = {
        recipient: { id: senderId },
        sender_action: "typing_off",
    };
    sendMessageToFacebook(messageData);
}

function sendMessageToFacebook(messageData) {
    axios
        .post(`https://graph.facebook.com/v12.0/me/messages?access_token=${PAGE_ACCESS_TOKEN}`, messageData)
        .then(() => console.log("Message envoyé !"))
        .catch((error) => console.error("Erreur d'envoi :", error.response ? error.response.data : error));
}

// Vérification toutes les heures pour envoyer un message automatique
setInterval(() => {
    let now = Date.now();
    for (let userId in userLastActivity) {
        if (now - userLastActivity[userId] > 3600000) { 
            sendOnlineStatusMessage(userId);
            delete userLastActivity[userId];
        }
    }
}, 60000);

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`✅ Serveur en ligne sur le port ${PORT}`));