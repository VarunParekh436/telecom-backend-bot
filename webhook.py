from flask import Flask, request, jsonify
import json

app = Flask(__name__)

with open("mock_database.json") as f:
    database = json.load(f)

def find_user(phone=None, email=None):
    for user in database:
        if phone and user["phone_number"] == phone:
            return user
        if email and user["email"] == email:
            return user
    return None

def compare_bills(bills, current_month):
    current = next((b for b in bills if b["month"] == current_month), None)
    if not current:
        return "No billing data found for this month."

    current_index = bills.index(current)
    previous = bills[current_index - 1] if current_index > 0 else None

    if not previous:
        return f"Your total bill for {current_month} is ${current['total']:.2f}."

    diff = current["total"] - previous["total"]
    explanation = f"Your bill increased by ${diff:.2f} from {previous['month']} to {current_month}.\n\n"
    explanation += "Here's a breakdown of the charges:\n"

    for key, value in current["charges"].items():
        explanation += f"- {key.replace('_', ' ').title()}: ${value:.2f}\n"

    return explanation

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    params = req.get("sessionInfo", {}).get("parameters", {})

    phone = params.get("phone_number")
    email = params.get("email")
    month = params.get("month")

    user = find_user(phone, email)
    if not user:
        return jsonify({
            "fulfillment_response": {
                "messages": [{"text": {"text": ["User not found. Please check your phone number or email."]}}]
            }
        })

    message = compare_bills(user["bills"], month)

    return jsonify({
        "fulfillment_response": {
            "messages": [{"text": {"text": [message]}}]
        }
    })

if __name__ == "__main__":
    app.run(port=5000)
