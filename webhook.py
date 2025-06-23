from flask import Flask, request, jsonify
import json

app = Flask(__name__)

with open("mock_database.json") as f:
    database = json.load(f)

def find_user(phone=None, email=None):
    print(f"Authenticating user with phone: {phone}, email: {email}")
    for user in database:
        if phone and email and user["phone_number"] == phone and user["email"] == email:
            print("✅ User authenticated successfully.")
            return user
    print("❌ Authentication failed.")
    return None

def compare_bills(bills, current_month):
    print(f"Comparing bills for month: {current_month}")
    current = next((b for b in bills if b["month"] == current_month), None)
    if not current:
        print("No billing data found for this month.")
        return "No billing data found for this month."
    current_index = bills.index(current)
    previous = bills[current_index - 1] if current_index > 0 else None
    if not previous:
        print(f"Only current month data available: {current_month}")
        return f"Your total bill for {current_month} is ${current['total']:.2f}."
    diff = current["total"] - previous["total"]
    explanation = f"Your bill increased by ${diff:.2f} from {previous['month']} to {current_month}.\n\n"
    explanation += "Here's a breakdown of the charges:\n"
    for key, value in current["charges"].items():
        explanation += f"- {key.replace('_', ' ').title()}: ${value:.2f}\n"
    print("Bill comparison complete.")
    return explanation

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    print("📥 Incoming request:", json.dumps(req, indent=2))
    params = req.get("sessionInfo", {}).get("parameters", {})
    phone = params.get("phone_number")
    email = params.get("email")
    month = params.get("month")

    user = find_user(phone, email)

    if not user:
        retry_count = params.get("retry_count", 0)
        retry_count += 1
        print(f"Retry count: {retry_count}")
        if retry_count >= 3:
            print("🚫 Too many failed attempts.")
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

    # ✅ User is authenticated
    if not month:
        print("🟡 Month not provided yet. Asking user for month.")
        return jsonify({
            "fulfillment_response": {
                "messages": [{"text": {"text": ["Authentication successful. What month would you like to compare?"]}}]
            },
            "sessionInfo": {
                "parameters": {
                    "authenticated": True
                }
            }
        })

    # ✅ Month is provided, compare bills
    print("🟢 Proceeding to bill comparison.")
    message = compare_bills(user["bills"], month)
    return jsonify({
        "fulfillment_response": {
            "messages": [{"text": {"text": [message]}}]
        }
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
