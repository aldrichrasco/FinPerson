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

# Only enforce HTTPS in production
if os.getenv("FLASK_ENV") == "production":
    Talisman(app, content_security_policy=csp)
else:
    Talisman(app, content_security_policy=csp, force_https=False)

# ✅ Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ✅ Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ ERROR: Missing OpenAI API Key. Set OPENAI_API_KEY in your environment variables.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Chatbot Personas Configuration
personas = {
    "saver": {"color": "#28a745", "icon": "💰", "description": "I encourage disciplined saving habits and long-term financial security."},
    "spender": {"color": "#dc3545", "icon": "🛍️", "description": "I provide budgeting tips and strategies to control impulse spending."},
    "investor": {"color": "#007bff", "icon": "📈", "description": "I offer insights into smart investing strategies and financial growth."},
    "avoider": {"color": "#6c757d", "icon": "🙈", "description": "I help users face financial management with confidence and overcome avoidance."},
    "giver": {"color": "#e83e8c", "icon": "❤️", "description": "I guide philanthropic financial planning while ensuring sustainability."},
    "planner": {"color": "#6610f2", "icon": "🗂️", "description": "I support structured financial goal-setting and long-term planning."},
    "risk_taker": {"color": "#fd7e14", "icon": "🎲", "description": "I advise on balancing risk and reward in financial decisions."},
    "security_seeker": {"color": "#343a40", "icon": "🔒", "description": "I reinforce strategies for financial stability and low-risk planning."}
}

# ✅ Serve Homepage
@app.route('/')
def home():
    return render_template("index.html")

# ✅ Serve Chatbot Persona Pages Using Jinja Template Inheritance
@app.route('/chat/<persona>')
def chat_page(persona):
    if persona not in personas:
        return "Chatbot persona not found", 404
    return render_template(
        f"{persona}.html",
        persona=persona,
        color=personas[persona]["color"],
        icon=personas[persona]["icon"],
        description=personas[persona]["description"]
    )

# ✅ Chat API: Handles User Messages & Stores in Firestore
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
            messages=[{"role": "system", "content": personas[persona]["description"]},
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

# ✅ Serve Static Files (Favicon, Images)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ✅ Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
