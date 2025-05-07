from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_talisman import Talisman  # Security middleware
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import datetime

# ✅ Load environment variables
load_dotenv()

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ Secure Content Security Policy (CSP)
csp = {
    'default-src': [
        "'self'",
        "https://*.firebaseio.com",
        "https://www.gstatic.com",
        "https://cdn.jsdelivr.net"
    ],
    'script-src': [
        "'self'",
        "https://www.gstatic.com",
        "https://cdnjs.cloudflare.com",
        "https://cdn.jsdelivr.net",
        "'unsafe-inline'",  # Allows inline scripts
        "'unsafe-eval'"  # Allows eval (needed for Firebase)
    ],
    'media-src': [
        "'self'",
        "https://www.myinstants.com"  # ✅ Allow sound files
    ],
    'style-src': [
        "'self'",
        "https://cdn.jsdelivr.net",
        "'unsafe-inline'"
    ],
    'img-src': [
        "'self'",
        "data:",
        "https://www.gstatic.com"
    ],
    'connect-src': [
        "'self'",
        "https://api.openai.com",
        "https://firestore.googleapis.com",
        "https://www.gstatic.com"
    ],
    'frame-src': [
        "'self'",
        "https://www.gstatic.com"
    ]
}

# ✅ Apply CSP Policy
Talisman(app, content_security_policy=csp)

# ✅ Initialize Firebase
cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ✅ Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ ERROR: Missing OpenAI API Key. Set OPENAI_API_KEY in your environment variables.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Chatbot Personas
personas = {
    "saver": "I encourage disciplined saving habits and long-term financial security.",
    "spender": "I provide budgeting tips and strategies to control impulse spending.",
    "investor": "I offer insights into smart investing strategies and financial growth.",
    "avoider": "I help users face financial management with confidence and overcome avoidance.",
    "giver": "I guide philanthropic financial planning while ensuring sustainability.",
    "planner": "I support structured financial goal-setting and long-term planning.",
    "risk_taker": "I advise on balancing risk and reward in financial decisions.",
    "security_seeker": "I reinforce strategies for financial stability and low-risk planning."
}

# ✅ Theme Colors for Chatbot Personalities
colors = {
    "saver": "#28a745",
    "spender": "#dc3545",
    "investor": "#007bff",
    "avoider": "#6c757d",
    "giver": "#e83e8c",
    "planner": "#6610f2",
    "risk_taker": "#fd7e14",
    "security_seeker": "#343a40"
}

# ✅ Chatbot Avatars
images = {
    "saver": "piggy_bank.png",
    "spender": "shopping_cart.png",
    "investor": "stock_chart.png",
    "avoider": "anxious.png",
    "giver": "heart.png",
    "planner": "calendar.png",
    "risk_taker": "dice.png",
    "security_seeker": "shield.png"
}

# ✅ Serve Homepage
@app.route('/')
def home():
    return render_template("index.html")

# ✅ Serve Chatbot Pages
@app.route('/chat/<persona>')
def chat_page(persona):
    if persona not in personas:
        return "Chatbot not found", 404
    return render_template("chat_template.html", persona=persona, persona_desc=personas[persona], colors=colors, images=images)

# ✅ Chat API: Handles user messages & stores in Firestore
@app.route('/chat_api/<persona>', methods=['POST'])
def chat(persona):
    if persona not in personas:
        return jsonify({"error": "Invalid chatbot persona"}), 400

    data = request.json
    user_id = data.get("user_id", "anonymous")
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": personas[persona]},
                      {"role": "user", "content": user_message}]
        )
        bot_reply = response.choices[0].message.content

        # ✅ Store chat history in Firestore with timestamp
        db.collection("chats").document(user_id).collection(persona).add({
            "user_message": user_message,
            "bot_reply": bot_reply,
            "timestamp": datetime.datetime.utcnow()
        })

        return jsonify({"response": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Retrieve Chat History
@app.route('/chat_history/<persona>')
def get_chat_history(persona):
    user_id = request.args.get("user_id", "anonymous")
    chats_ref = db.collection("chats").document(user_id).collection(persona)
    chats = chats_ref.order_by("timestamp").stream()

    chat_history = [{"user_message": chat.get("user_message"), "bot_reply": chat.get("bot_reply")} for chat in chats]
    return jsonify(chat_history)

# ✅ Serve Static Files Like Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ✅ Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
