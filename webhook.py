from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Load mock database
with open("mock_database.json") as f:
    database = json.load(f)

def normalize_phone(phone):
    if not phone:
        return ""
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

# Format charges into a user-friendly bullet list
def format_charges(charges):
    return '\n'.join([
        f"• {key.replace('_', ' ').title()}: ${value:.2f}"
        for key, value in charges.items()
    ])

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    params = req
    print("Parameters received:", params)

    phone = params.get("phone_number") or params.get("phone")
    email = params.get("email")
    user = find_user(phone, email)

    if not user:
        retry_count = params.get("retry_count", 0) + 1
        return jsonify({
            "sessionInfo": {
                "parameters": {
                    "authenticated": False,
                    "retry_count": retry_count
                }
            }
        })
    
    if not params.get("authenticated", False):
        return jsonify({
            "sessionInfo": {
                "parameters": {
                    "authenticated": True,
                    "phone_number": phone,
                    "email": email, 
                    "retry_count": params.get("retry_count", 0)
                }
            }
        })

    # Always return bill data if authenticated
    bills = user.get("bills", [])
    if len(bills) < 1:
        return jsonify({
            "sessionInfo": {
                "parameters": {
                    "bill_data_available": False
                }
            }
        })

    latest = bills[-1]
    previous = bills[-2] if len(bills) > 1 else None

    formatted_latest = format_charges(latest["charges"])
    formatted_previous = format_charges(previous["charges"]) if previous else None

    return jsonify({
        "sessionInfo": {
            "parameters": {
                "bill_data_available": True,
                "latest_month": latest["month"],
                "latest_total": latest["total"],
                "latest_charges": latest["charges"],
                "formatted_latest_charges": formatted_latest,
                "previous_month": previous["month"] if previous else None,
                "previous_total": previous["total"] if previous else None,
                "previous_charges": previous["charges"] if previous else None,
                "formatted_previous_charges": formatted_previous,
                "bill_difference": round(latest["total"] - previous["total"], 2) if previous else None
            }
        }
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
