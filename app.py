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
    "steady_saver": "I encourage disciplined saving habits and long-term financial security.",
    "conscious_spender": "I provide budgeting tips and strategies to control impulse spending.",
    "ambitious_builder": "I offer insights into smart investing strategies and financial growth.",
    "anxious_avoider": "I help users face financial management with confidence and overcome avoidance.",
    "purposeful_giver": "I guide philanthropic financial planning while ensuring sustainability.",
    "strategic_risk_taker": "I advise on balancing risk and reward in financial decisions.",
    "cautious_guardian": "I reinforce strategies for financial stability and low-risk planning.",
    "impulsive_spender": "I help develop mindful spending habits and break free from impulsive cycles.",
    "overconfident_navigator": "I challenge assumptions and encourage reflection to avoid overestimating financial knowledge.",
    "status_seeker": "I shift focus from outward image to authentic, sustainable financial goals.",
    "passive_drifter": "I help users re-engage and take ownership of their financial journey."
}


colors = {
    "steady_saver": "#28a745",
    "conscious_spender": "#dc3545",
    "ambitious_builder": "#007bff",
    "anxious_avoider": "#6c757d",
    "purposeful_giver": "#e83e8c",
    "strategic_risk_taker": "#fd7e14",
    "cautious_guardian": "#343a40",
    "impulsive_spender": "#ff5722",
    "overconfident_navigator": "#f0ad4e",
    "status_seeker": "#6610f2",
    "passive_drifter": "#adb5bd"
}


images = {
    "steady_saver": "piggy_bank.png",
    "conscious_spender": "shopping_cart.png",
    "ambitious_builder": "stock_chart.png",
    "anxious_avoider": "anxious.png",
    "purposeful_giver": "heart.png",
    "strategic_risk_taker": "dice.png",
    "cautious_guardian": "shield.png",
    "impulsive_spender": "warning_sign.png",
    "overconfident_navigator": "telescope.png",
    "status_seeker": "trophy.png",
    "passive_drifter": "cloud.png"
}


# Routes
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/chat_api/<persona>', methods=['GET', 'POST'])
def chat_page(persona):
    if persona not in personas:
        if request.method == 'GET':
            return "Chatbot not found", 404
        return jsonify({"error": "Invalid chatbot persona"}), 400

    if request.method == 'GET':
        return render_template(
            "chat_template.html",
            persona=persona,
            persona_desc=personas[persona],
            colors=colors,
            images=images
        )

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
                {"role": "user", "content": user_message + " but keep it short - maximum 30 words"}
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
        persona = request.args.get("persona", "steady_saver")

        # Generate session stats
        stats = {
            "income": random_start(),
            "expenses": random_start(),
            "savings": random_start(),
            "investments": random_start(),
            "debt": random_start()
        }

        scenario, increments, category = generate_financial_prompt_and_increments(difficulty, stats, persona)
        actions = generate_action_options(scenario, increments, persona)

        metrics = calculate_financial_metrics(stats)

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
            "metrics": metrics
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

def generate_financial_prompt_and_increments(difficulty, stats, persona):
    try:
        category = random.choice(categories)
        effect = random.randint(-10000, 10000) if difficulty == "hard" else (
            random.randint(-1000, 1000) if difficulty == "medium" else random.randint(-100, 100)
        )

        persona_desc = personas.get(persona, "")

        financial_snapshot = (
            f"User Profile: {persona} — {persona_desc}\n"
            f"Current Stats:\n"
            f"- Income: ${stats['income']:.2f}\n"
            f"- Expenses: ${stats['expenses']:.2f}\n"
            f"- Savings: ${stats['savings']:.2f}\n"
            f"- Investments: ${stats['investments']:.2f}\n"
            f"- Debt: ${stats['debt']:.2f}\n"
        )

        prompt = (
            f"{financial_snapshot}\n"
            f"Based on this profile, write a short realistic financial scenario involving '{category}' "
            f"with a simulated effect of {effect}. Keep it under 30 words."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful financial simulator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=60
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


def generate_action_options(scenario, increments, persona):
    persona_desc = personas.get(persona, "")
    actions = []

    for inc in increments:
        prompt = (
            f"Persona: {persona} — {persona_desc}\n"
            f"Scenario: {scenario}\n"
            f"Impact: {inc['increment']} on the financial category.\n"
            f"Suggest a financial action this persona is likely to take, under 25 words."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            action = response.choices[0].message.content.strip()
        except Exception:
            action = f"Mock action for {persona} with {inc['risk_level']}."

        actions.append({"risk_level": inc["risk_level"], "action": action})
    return actions


# Define clearly and once

def calculate_financial_metrics(stats):
    # Avoid division by zero
    def safe_div(x, y): return round(x / (y + 1), 2)

    emergency_fund_ratio = safe_div(stats["savings"], stats["expenses"])  # in months
    debt_to_income_ratio = safe_div(stats["debt"], stats["income"])       # %
    asset_to_debt_ratio = safe_div(
        stats["income"] + stats["savings"] + stats["investments"], abs(stats["debt"]))  # ratio
    retirement_savings_ratio = safe_div(stats["investments"], stats["income"])  # proxy for retirement

    return {
        "emergency_fund_ratio": emergency_fund_ratio,
        "debt_to_income_ratio": debt_to_income_ratio,
        "asset_to_debt_ratio": asset_to_debt_ratio,
        "retirement_savings_ratio": retirement_savings_ratio
    }

    
@app.route('/get_advice_for_action', methods=['POST'])
def get_advice_for_action():
    try:
        data = request.get_json()
        choice_index = int(data.get("choice", 0))
        persona = data.get("persona", "steady_saver")
        persona_desc = personas.get(persona, "This user has no defined persona.")

        action = current_session["actions"][choice_index]
        increment = current_session["increments"][choice_index]
        category = current_session.get("category", "income")
        metrics = calculate_financial_metrics(current_session["stats"])

        # Compose financial metric summary
        metric_summary = (
            f"- Emergency Fund Ratio: {metrics['emergency_fund_ratio']} months\n"
            f"- Debt-to-Income Ratio: {metrics['debt_to_income_ratio'] * 100:.1f}%\n"
            f"- Asset-to-Debt Ratio: {metrics['asset_to_debt_ratio']}\n"
            f"- Retirement Savings Ratio: {metrics['retirement_savings_ratio']}\n"
        )

        prompt = (
            f"The user chose an action: '{action['action']}' which affects the {category} category by {increment['increment']}.\n"
            f"Their current financial stats are:\n{metric_summary}\n\n"
            f"Persona: {persona} — {persona_desc}\n"
            f"Write a personalized wellbeing analysis and financial advice for this user. Reflect on their tendencies, highlight risks or strengths, and suggest next steps.\n"
            f"Length: 80–150 words. Tone: practical and empathetic."
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial coach who gives concise, insightful, and persona-aligned advice."},
                {"role": "user", "content": prompt}
            ]
        )

        advice = response.choices[0].message.content.strip()
        return jsonify({"advice": advice})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)