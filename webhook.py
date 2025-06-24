from flask import Flask, request, jsonify
import json

app = Flask(__name__)

with open("mock_database.json") as f:
    database = json.load(f)

def find_user(phone=None, email=None):
    print(f"Authenticating user with phone: {phone}, email: {email}")
    for user in database:
        if phone and email and user["phone_number"] == phone and user["email"] == email:
            print("User authenticated successfully.")
            return user
    print("Authentication failed.")
    return None

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

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
