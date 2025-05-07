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
