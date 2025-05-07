from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_talisman import Talisman  # Security middleware
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import os
import random
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

@app.route("/dashboard")
def dashboard():
    return render_template("findashboard.html")

from flask import session

# ✅ Set secret key if using session
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")

# ✅ Default financial template
def default_financial_data():
    return {
        "income": 7500,
        "expenses": 4000,
        "savings": 15000,
        "investments": 10000,
        "debt": 8500
    }

@app.before_request
def initialize_user_session():
    if 'financial_data' not in session:
        session['financial_data'] = default_financial_data()
        session['previous_data'] = default_financial_data()
        session['scenario_history'] = []

@app.route("/get_random_scenario", methods=["GET"])
def get_random_scenario():
    difficulty = request.args.get("difficulty", "medium")
    prompt = f"Generate a very short financial scenario based on a {difficulty} difficulty level. Keep it concise, under 15 words."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial simulation assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20
        )
        scenario = response.choices[0].message.content.strip()
    except Exception:
        scenario = "Unexpected change in your financial situation."

    action_prompt = f"Generate three short multiple-choice financial actions for this scenario: '{scenario}'."
    try:
        action_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You generate financial decision-making choices."},
                {"role": "user", "content": action_prompt}
            ],
            max_tokens=50
        )
        actions = action_response.choices[0].message.content.strip().split("\n")
    except Exception:
        actions = [
            "Option A: Adjust budget",
            "Option B: Take on extra work",
            "Option C: Use emergency savings"
        ]

    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    session['scenario_history'].append({
        "scenario": scenario,
        "difficulty": difficulty,
        "time": timestamp,
        "actions": actions
    })
    session['last_actions'] = actions
    return jsonify({"scenario": scenario, "actions": actions})

@app.route("/process_user_choice", methods=["GET"])
def process_user_choice():
    choice = request.args.get("choice")
    financial_data = session.get("financial_data", default_financial_data())
    previous_data = financial_data.copy()

    action_index = {"A": 0, "B": 1, "C": 2}.get(choice, 0)
    chosen_action = session.get("last_actions", ["", "", ""])[action_index].lower()

    impact_map = {
        'income': 0,
        'expenses': 0,
        'savings': 0,
        'investments': 0,
        'debt': 0
    }

    if "income" in chosen_action or "gig" in chosen_action or "job" in chosen_action:
        impact_map['income'] += 500
    if "spend" in chosen_action or "budget" in chosen_action or "cut" in chosen_action:
        impact_map['expenses'] -= 300
    if "emergency fund" in chosen_action or "savings" in chosen_action:
        impact_map['savings'] -= 2000
    if "invest" in chosen_action:
        impact_map['investments'] += 200
    if "loan" in chosen_action or "credit" in chosen_action:
        impact_map['debt'] += 1000

    for key, delta in impact_map.items():
        financial_data[key] = max(0, financial_data[key] + delta)

    session["previous_data"] = previous_data
    session["financial_data"] = financial_data

    change_summary = {}
    for k in financial_data:
        change = financial_data[k] - previous_data[k]
        arrow = "🟢" if change >= 0 else "🔴"
        percent = (change / previous_data[k]) * 100 if previous_data[k] != 0 else 0
        change_summary[k] = f"{arrow} {change} ({percent:.1f}%)"

    recommendation_prompt = f"User chose '{chosen_action}' for scenario: '{session['scenario_history'][-1]['scenario']}'. Give a brief financial recommendation."
    try:
        rec_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You generate financial advice based on user decisions."},
                {"role": "user", "content": recommendation_prompt}
            ],
            max_tokens=50
        )
        recommendation = rec_response.choices[0].message.content.strip()
    except Exception:
        recommendation = "Consider saving more or reducing discretionary spending."

    # Risk assessment
    risk_score = 0
    if financial_data['savings'] < 10000:
        risk_score += 2
    if financial_data['debt'] > 0.5 * financial_data['income']:
        risk_score += 2
    if financial_data['expenses'] > 0.75 * financial_data['income']:
        risk_score += 1
    status = "High Risk" if risk_score >= 4 else "Moderate Risk" if risk_score >= 2 else "Stable"

    # Update scenario history
    session['scenario_history'][-1]["selected_action"] = chosen_action
    session['scenario_history'][-1]["result_status"] = status

    return jsonify({
        "previousMetrics": previous_data,
        "metrics": financial_data,
        "status": status,
        "summary": f"You selected Option {choice}.",
        "changeSummary": change_summary,
        "recommendations": recommendation,
        "confidence": random.randint(75, 95),
        "scenarioHistory": session['scenario_history']
    })

@app.route("/undo_last_action", methods=["GET"])
def undo_last_action():
    session["financial_data"] = session["previous_data"]
    return jsonify({
        "previousMetrics": session["previous_data"],
        "metrics": session["financial_data"],
        "status": "Stable",
        "summary": "Reverted to previous financial state.",
        "changeSummary": "Undo successful.",
        "recommendations": "Your previous state has been restored.",
        "confidence": random.randint(80, 98)
    })

# ✅ Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
