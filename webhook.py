from flask import Flask, request, jsonify
import json

app = Flask(__name__)

with open("mock_database.json") as f:
    database = json.load(f)

def normalize_phone(phone):
    return phone.replace("+", "").replace("-", "").replace(" ", "")

def find_user(phone=None, email=None):
    print(f"Authenticating user with phone: '{phone}', email: '{email}'")
    phone = normalize_phone(phone)
    for user in database:
        db_phone = normalize_phone(user["phone_number"])
        if phone and email and db_phone == phone and user["email"] == email:
            print("User authenticated successfully.")
            return user
    print("Authentication failed.")
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
    print("Parameters received:", params)

    # Try both possible keys for phone number
    phone = params.get("phone_number") or params.get("phone")
    email = params.get("email")


    user = find_user(phone, email)

    if not user:
        retry_count = params.get("retry_count", 0)
        retry_count += 1
        print(f"Authentication failed. Retry count: {retry_count}")
        if retry_count >= 3:
            print("Too many failed attempts.")
            return jsonify({
                "fulfillment_response": {
                    "messages": [{"text": {"text": ["Authentication failed multiple times. Please contact support."]}}]
                },
                "sessionInfo": {
                    "parameters": {
                        "authenticated": False,
                        "retry_count": retry_count
                    }
                }
            })
        return jsonify({
            "fulfillment_response": {
                "messages": [{"text": {"text": ["Authentication failed. Please check your phone number or email."]}}]
            },
            "sessionInfo": {
                "parameters": {
                    "authenticated": False,
                    "retry_count": retry_count
                }
            }
        })

    #Authentication successful
    print("Authentication successful. Moving to next step.")
    if not params.get("authenticated"):
        return jsonify({
            "fulfillment_response": {
                "messages": [{"text": {"text": ["Authentication successful. How can I help you today?"]}}]
            },
            "sessionInfo": {
                "parameters": {
                    "authenticated": True
                }
            }
        })

    # Check if user is asking for bill comparison
    intent = req.get("intentInfo", {}).get("lastMatchedIntent", "")
    if intent == "CompareBillsIntent":
        print("CompareBillsIntent matched.")
        bills = user.get("bills", [])
        if len(bills) < 1:
            return jsonify({
                "fulfillment_response": {
                    "messages": [{"text": {"text": ["No billing history available."]}}]
                }
            })
        latest_month = bills[-1]["month"]
        message = compare_bills(bills, latest_month)
        return jsonify({
            "fulfillment_response": {
                "messages": [{"text": {"text": [message]}}]
            }
        })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
