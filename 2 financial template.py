from flask import Flask, request, jsonify, session, render_template
from flask_talisman import Talisman
from flask_session import Session
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import os
import random
import traceback
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Secure CSP
csp = {
    'default-src': ["'self'", "https://*.firebaseio.com", "https://www.gstatic.com", "https://cdn.jsdelivr.net"],
    'script-src': ["'self'", "https://www.gstatic.com", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net", "'unsafe-inline'", "'unsafe-eval'"],
    'media-src': ["'self'", "https://www.myinstants.com"],
    'style-src': ["'self'", "https://cdn.jsdelivr.net", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "https://www.gstatic.com"],
    'connect-src': ["'self'", "https://api.openai.com", "https://firestore.googleapis.com", "https://www.gstatic.com"],
    'frame-src': ["'self'", "https://www.gstatic.com"]
}
Talisman(app, content_security_policy=csp, force_https=False)

# Firebase & OpenAI setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Chatbot configuration
def random_start():
    return round(random.uniform(-5000, 25000), 2)

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

colors = {
    "saver": "#28a745", "spender": "#dc3545", "investor": "#007bff", "avoider": "#6c757d",
    "giver": "#e83e8c", "planner": "#6610f2", "risk_taker": "#fd7e14", "security_seeker": "#343a40"
}

images = {
    "saver": "piggy_bank.png", "spender": "shopping_cart.png", "investor": "stock_chart.png",
    "avoider": "anxious.png", "giver": "heart.png", "planner": "calendar.png",
    "risk_taker": "dice.png", "security_seeker": "shield.png"
}

# Routes
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/chat_api/<persona>')
def chat_page(persona):
    if persona not in personas:
        return "Chatbot not found", 404
    return render_template("chat_template.html", persona=persona, persona_desc=personas[persona], colors=colors, images=images)

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
        print(f"Sending to GPT: {user_message}")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": personas[persona]},
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = response.choices[0].message.content
        print(f"GPT says: {bot_reply}")

        db.collection("chats").document(user_id).collection(persona).add({
            "user_message": user_message,
            "bot_reply": bot_reply,
            "timestamp": datetime.datetime.utcnow()
        })

        return jsonify({"response": bot_reply})
    except Exception as e:
        print("Internal Server Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/chat_history/<persona>')
def get_chat_history(persona):
    user_id = request.args.get("user_id", "anonymous")
    chats_ref = db.collection("chats").document(user_id).collection(persona)
    chats = chats_ref.order_by("timestamp").stream()

    chat_history = [{"user_message": chat.get("user_message"), "bot_reply": chat.get("bot_reply")} for chat in chats]
    return jsonify(chat_history)

def random_start():
    return round(random.uniform(1000, 10000), 2)  # generates random float between 1000 and 10000

@app.route('/dashboard')
def dashboard():
    current_session = {
        "scenario": None,
        "increments": [],
        "actions": [],
        "category": None,
        "stats": {
            "income": random_start(),
            "expenses": random_start(),
            "savings": random_start(),
            "investments": random_start(),
            "debt": random_start()
        }
    }
    # Pass current_session into the template
    return render_template('findashboard.html', current_session=current_session)

@app.route('/get_session', methods=['GET'])
def get_session():
    try:
        return jsonify(current_session)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
# Ensure to integrate clearly into your existing Flask app

@app.route('/get_scenario', methods=['GET'])
def get_scenario():
    try:
        difficulty = request.args.get("difficulty", "medium")
        scenario, increments, category = generate_financial_prompt_and_increments(difficulty)
        actions = generate_action_options(scenario, increments)

        stats = {
            "income": random_start(),
            "expenses": random_start(),
            "savings": random_start(),
            "investments": random_start(),
            "debt": random_start()
        }

        metrics = calculate_financial_metrics(stats)  # clearly calculated metrics

        current_session.update({
            "scenario": scenario,
            "increments": increments,
            "actions": actions,
            "category": category,
            "stats": stats
        })

        return jsonify({
            "scenario": scenario,
            "actions": actions,
            "increments": increments,
            "category": category,
            "stats": stats,
            "metrics": metrics  # clearly added
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/process_action', methods=['POST'])
def process_action():
    try:
        data = request.get_json()
        choice = int(data.get("choice", 0))
        inc = current_session["increments"][choice]
        act = current_session["actions"][choice]
        category = current_session.get("category", "income")

        delta = inc["increment"]
        old_value = current_session["stats"].get(category, 0)
        min_allowed = stat_thresholds.get(category, -10000)
        new_value = max(old_value + delta, min_allowed)

        current_session["stats"][category] = new_value
        direction = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")

        metrics = calculate_financial_metrics(current_session["stats"])  # clearly calculate metrics

        return jsonify({
            "assessment": f"Applied {inc['risk_level'].replace('_', ' ').title()} action.",
            "change_summary": f"{direction} {category.title()} changed by {delta:.2f}.",
            "recommendations": act["action"],
            "stats": current_session["stats"],
            "metrics": metrics
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Helpers and Logic
current_session = {
    "scenario": None,
    "increments": [],
    "actions": [],
    "category": None,
    "stats": {
        "income": random_start(),
        "expenses": random_start(),
        "savings": random_start(),
        "investments": random_start(),
        "debt": random_start()
    }
}

stat_thresholds = {
    "income": -1000,
    "expenses": -500,
    "savings": -2000,
    "investments": -3000,
    "debt": -20000
}

categories = ["income", "expenses", "savings", "investments", "debt"]
risk_levels = ["low_risk", "medium_risk", "high_risk"]
risk_multipliers = {
    "low_risk": (0.9, 1.1),
    "medium_risk": (1.1, 2.0),
    "high_risk": (2.0, 5.0)
}

def generate_financial_prompt_and_increments(difficulty):
    try:
        category = random.choice(categories)
        effect = random.randint(-10000, 10000) if difficulty == "hard" else (
            random.randint(-1000, 1000) if difficulty == "medium" else random.randint(-100, 100)
        )
        prompt = f"With this {category} and this numerical effect of {effect}, generate a concise financial scenario in 15 words or less."
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50
            )
            scenario = response.choices[0].message.content.strip()
        except Exception:
            scenario = f"Mock scenario: {category} changed by {effect}."
        increments = [
            {"risk_level": r, "increment": round(effect * random.uniform(*risk_multipliers[r]), 2)}
            for r in risk_levels
        ]
        return scenario, increments, category
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError("Failed to generate scenario.")

def generate_action_options(scenario, increments):
    actions = []
    for inc in increments:
        prompt = f"Given '{scenario}' and impact of {inc['increment']}, suggest a financial action."
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            action = response.choices[0].message.content.strip()
        except Exception:
            action = f"Mock action: Adjust your {inc['risk_level']} strategy."
        actions.append({"risk_level": inc["risk_level"], "action": action})
    return actions

# Define clearly and once

def calculate_financial_metrics(stats):
    emergency_fund_ratio = round(stats["savings"] / (stats["expenses"] + 1), 2)
    debt_to_income_ratio = round(abs(stats["debt"] / (stats["income"] + 1)), 2)
    savings_rate = round(stats["savings"] / (stats["income"] + 1), 2)

    return {
        "emergency_fund_ratio": emergency_fund_ratio,
        "debt_to_income_ratio": debt_to_income_ratio,
        "savings_rate": savings_rate
    }

if __name__ == '__main__':
    app.run(debug=True)