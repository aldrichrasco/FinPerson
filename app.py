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
import threading

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure session type
app.config['SESSION_TYPE'] = 'filesystem'

# ✅ Add this line to avoid the 'session_cookie_name' error
app.config['SESSION_COOKIE_NAME'] = 'session'

# Initialize Flask-Session
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

persona_voice_map = {
    "steady_saver": {
        "tone": "disciplined",
        "emotion": "stability",
        "guidance": "Calm, consistent, values routine and long-term planning."
    },
    "conscious_spender": {
        "tone": "intentional",
        "emotion": "control",
        "guidance": "Carefully weighs options, avoids unnecessary excess, values clarity."
    },
    "ambitious_builder": {
        "tone": "driven",
        "emotion": "ambition",
        "guidance": "Optimistic and goal-focused, seeks to maximize growth."
    },
    "anxious_avoider": {
        "tone": "hesitant",
        "emotion": "fear",
        "guidance": "Worried and self-doubting, avoids tough decisions but knows change is needed."
    },
    "purposeful_giver": {
        "tone": "compassionate",
        "emotion": "empathy",
        "guidance": "Motivated by helping others, seeks meaning, often puts others first."
    },
    "strategic_risk_taker": {
        "tone": "confident",
        "emotion": "risk",
        "guidance": "Analytical, bold, and confident — not afraid to act."
    },
    "cautious_guardian": {
        "tone": "protective",
        "emotion": "caution",
        "guidance": "Wary of change, prefers safety, questions risky actions."
    },
    "impulsive_spender": {
        "tone": "impulsive",
        "emotion": "regret",
        "guidance": "Acts on emotion, wants satisfaction now, often apologetic after."
    },
    "overconfident_navigator": {
        "tone": "assertive",
        "emotion": "pride",
        "guidance": "Bold, assumes they’re right, focuses on results — not always realistic."
    },
    "status_seeker": {
        "tone": "image-conscious",
        "emotion": "insecurity",
        "guidance": "Wants recognition, status-driven, fears judgment, frames in terms of perception."
    },
    "passive_drifter": {
        "tone": "disengaged",
        "emotion": "detachment",
        "guidance": "Passive voice, unsure, prefers comfort, avoids strong positions."
    },
    "generous_giver": {
        "tone": "selfless",
        "emotion": "joy",
        "guidance": "Gentle, sacrificial, always thinking about others' wellbeing first."
    }
}

# 👇 GLOBAL VARIABLES — Define once near the top
categories = ["income", "expenses", "savings", "investments", "debt"]

risk_levels = ["low_risk", "medium_risk", "high_risk"]

risk_multipliers = {
    "low_risk": (0.9, 1.1),
    "medium_risk": (1.1, 2.0),
    "high_risk": (2.0, 5.0)
}

stat_thresholds = {
    "income": -1000,
    "expenses": -500,
    "savings": -2000,
    "investments": -3000,
    "debt": -20000
}

# Global session state
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

    # POST - handle incoming message
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
                {"role": "user", "content": user_message + "reply like a human in one paragaph related to the persona"}
            ]
        )
        bot_reply = response.choices[0].message.content
        print(f"GPT says: {bot_reply}")
        return jsonify({"response": bot_reply})

    except Exception as e:
        print("Internal Server Error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/chat_api/<persona>/end', methods=['POST'])
def save_chat_session(persona):
    print(f"🔥 POST /chat_api/{persona}/end received")  
    if persona not in personas:
        return jsonify({"error": "Invalid chatbot persona"}), 400

    data = request.json
    user_id = data.get("user_id", "anonymous")
    chat_history = data.get("chat_history", [])

    try:
        db.collection("chats").document(user_id).collection(persona).add({
            "history": chat_history,
            "timestamp": datetime.datetime.utcnow()
        })
        print(f"✅ Session stored under chats/{user_id}/{persona}")
        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Firestore session log failed:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/chat_history/<persona>')
def get_chat_history(persona):
    user_id = request.args.get("user_id", "anonymous")
    chats_ref = db.collection("chat_sessions").where("user_id", "==", user_id).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()

    for chat in chats_ref:
        return jsonify(chat.to_dict().get("history", []))
    return jsonify([])

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

def build_persona_prompt(persona, scenario, increment, category):
    persona_info = persona_voice_map.get(persona, {
        "tone": "neutral",
        "emotion": "unclear",
        "guidance": "Speak in a practical and emotionally neutral tone."
    })

    tone = persona_info["tone"]
    emotion = persona_info["emotion"]
    guidance = persona_info["guidance"]

    return f"""
Persona: {persona.replace('_', ' ').title()}
Tone: {tone}
Dominant Emotion: {emotion}
Emotional Voice Guidance: {guidance}

Scenario: {scenario}
Category Impacted: {category}
Effect Value: {increment}

Create THREE decision options this persona might realistically have.
Each option must include:
1. A 5–10 word internal monologue (first person and reflective)
2. A concise action description (what they would do)
3. One primary metric affected (Income/Expenses/Savings/Investments/Debt)
4. The numerical delta to that metric (e.g., +0.45)
5. A tone tag (e.g., confident, anxious, impulsive)

Format exactly:
Option 1
Monologue:
Action:
Metric:
Delta:
Tone:

Option 2
Monologue:
Action:
Metric:
Delta:
Tone:

Option 3
Monologue:
Action:
Metric:
Delta:
Tone:

Keep total response under 40 words. Do not explain. Just output the options directly.
"""


@app.route('/get_scenario', methods=['GET'])
def get_scenario():
    try:
        difficulty = request.args.get("difficulty", "medium")
        persona = request.args.get("persona", "steady_saver")

        raw_stats = {
            "income": random_start(),
            "expenses": random_start(),
            "savings": random_start(),
            "investments": random_start(),
            "debt": random_start()
        }

        # Convert to floats safely
        stats = {}
        for key in raw_stats:
            try:
                stats[key] = float(raw_stats[key])
            except (TypeError, ValueError):
                stats[key] = 0.0

        scenario, increments, category = generate_financial_prompt_and_increments(difficulty, stats, persona)
        increment = increments[1]  # medium risk by default
        actions = generate_all_actions(scenario, increment["increment"], category, persona)
        metrics = calculate_financial_metrics(stats)

        # Validate and fix missing keys
        required_keys = {"action", "behavior", "primary_metric", "primary_delta", "tone"}
        for i, act in enumerate(actions):
            for key in required_keys:
                if key not in act or act[key] is None:
                    print(f"[Warning] Missing '{key}' in action {i+1}, setting fallback.")
                    act.setdefault("action", "No monologue.")
                    act.setdefault("behavior", "No behavior provided.")
                    act.setdefault("primary_metric", "Savings")
                    act.setdefault("primary_delta", 0.0)
                    act.setdefault("tone", "neutral")

        # Fallback mock actions if needed
        if not actions or len(actions) < 3:
            print("[Fallback] Using mock actions due to insufficient or bad response.")
            actions = [
                {
                    "action": "Mock reflection",
                    "behavior": "Fallback action",
                    "primary_metric": "Savings",
                    "primary_delta": 100.0 * i,
                    "tone": "neutral",
                    "intensity": "medium",
                    "has_conflict": False
                }
                for i in range(1, 4)
            ]

        # Cap rules for stats
        stat_caps = {
            "debt": 0.0,
            "expenses": 0.0,
            "income": 0.0,
            "savings": 0.0,
            "investments": 0.0
        }
        for stat, minimum in stat_caps.items():
            if stats.get(stat, 0) < minimum:
                stats[stat] = minimum

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

        # Cap rules for stats (apply after update)
        stat_caps = {
            "debt": 0.0,
            "expenses": 0.0,
            "income": 0.0,
            "savings": 0.0,
            "investments": 0.0
        }
        for stat, minimum in stat_caps.items():
            if current_session["stats"].get(stat, 0) < minimum:
                current_session["stats"][stat] = minimum

        direction = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")
        metrics = calculate_financial_metrics(current_session["stats"])

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
                max_tokens=100
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


import random

# Updated generate_all_actions function using the new GPT prompt and parser
def generate_all_actions(scenario, increment, category, persona):
    try:
        prompt = build_persona_prompt(persona, scenario, increment, category)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )

        response_text = response.choices[0].message.content.strip()
        print("RAW GPT RESPONSE:\n", response_text)

        pattern = re.compile(
            r"Option \d+\s*"
            r"Monologue:\s*(.*?)\s*"
            r"Action:\s*(.*?)\s*"
            r"Metric:\s*(.*?)\s*"
            r"Delta:\s*([+-]?[0-9]*\.?[0-9]+)\s*"
            r"Tone:\s*(.*?)\s*",
            re.IGNORECASE | re.DOTALL
        )

        matches = pattern.findall(response_text)
        actions = []
        for match in matches:
            monologue, action, metric, delta, tone = match
            actions.append({
                "action": monologue.strip(),
                "behavior": action.strip(),
                "primary_metric": metric.strip().capitalize(),
                "primary_delta": float(delta),
                "tone": tone.strip().lower()
            })

        return actions

    except Exception as e:
        print("GPT fallback activated:", e)
        traceback.print_exc()
        return [
            {
                "action": f"Fallback thought {i}",
                "behavior": f"Fallback action {i}",
                "primary_metric": "Savings",
                "primary_delta": 100 * i,
                "tone": "neutral"
            } for i in range(1, 4)
        ]



import re

def parse_gpt_response(response_text):
    pattern = re.compile(
        r"Option (\d+)\s*"
        r"Monologue:\s*(.*?)\s*"
        r"Action:\s*(.*?)\s*"
        r"Metric:\s*(.*?)\s*"
        r"Delta:\s*([+-]?[0-9]*\.?[0-9]+)\s*"
        r"Tone:\s*(.*?)\s*"
        r"Intensity:\s*(.*?)\s*"
        r"Conflict:\s*(true|false)",
        re.IGNORECASE | re.DOTALL
    )

    options = []
    matches = pattern.findall(response_text)

    for match in matches:
        option_number, monologue, action, metric, delta, tone, intensity, conflict = match
        options.append({
            "option": int(option_number),
            "action": monologue.strip(),  # this is the internal monologue
            "behavior": action.strip(),   # what they actually do
            "primary_metric": metric.strip(),
            "primary_delta": float(delta),
            "tone": tone.strip().lower(),
            "intensity": intensity.strip().lower(),
            "has_conflict": conflict.strip().lower() == "true"
        })

    return options

def extract_option_block(response_text, option_number):
    import re
    pattern = re.compile(
        rf"Option {option_number}.*?A\)\s*(.*?)\s*B\)\s*(.*?)\s*C\)\s*(.*?)\s*D\)\s*(.*?)($|\nOption|\Z)",
        re.DOTALL | re.IGNORECASE
    )
    match = pattern.search(response_text)
    if match:
        return tuple(part.strip() for part in match.groups()[:4])
    return None



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

@app.route('/get_persona_metadata', methods=['GET'])
def get_persona_metadata():
    try:
        simplified_data = {
            persona: {
                "tone": data.get("tone"),
                "emotion": data.get("emotion"),
                "guidance": data.get("guidance"),
                "taglines": data.get("taglines", [])
            }
            for persona, data in persona_voice_map.items()
        }
        return jsonify(simplified_data)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
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
    
@app.route('/test_firestore')
def test_firestore():
    try:
        # Manual test write
        db.collection("chats").document("anonymous").collection("ambitious_builder").add({
            "user_message": "Test user msg",
            "bot_reply": "Test bot reply",
            "timestamp": datetime.datetime.utcnow()
        })

        # Manual test read
        chats = db.collection("chats").document("anonymous").collection("ambitious_builder").order_by("timestamp").stream()
        messages = [chat.to_dict() for chat in chats]

        return jsonify(messages)

    except Exception as e:
        return jsonify({"error": str(e)})
    
db.collection("chats").document("test_user").collection("saver").add({
    "user_message": "Manual test",
    "bot_reply": "Hello from saver!",
    "timestamp": datetime.datetime.utcnow()
})


def safe_div(x, y):
    return round(x / (y + 1e-6), 2)

if __name__ == '__main__':
    app.run(debug=True)
