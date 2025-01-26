from flask import Flask, render_template, request, redirect, url_for
import requests
from flask import jsonify

import segment.analytics as analytics
import datetime
import dotenv
import random
import dummies

# Load the environment variables
WRITE_KEY = dotenv.get_key('.env', 'WRITE_KEY')
PORTAL_ID = dotenv.get_key('.env', 'HUBSPOT_PORTAL_ID')

# Set up the analytics client
analytics.write_key = WRITE_KEY

def random_string(length):
    return ''.join(random.choice('0123456789ABCDEF') for i in range(length)).lower()

app = Flask(__name__)

# Track an item purchased event
def track_page_visited(id, route):
    return analytics.track(id, 'Page Visited', {
    'route': route,
    })

def track_event(id, event_name, properties):
    return analytics.track(id, event_name, properties)

# Make portal_id globally available in templates
@app.context_processor
def inject_portal_id():
    return {'portal_id': PORTAL_ID}

# Home page route
@app.route('/')
def home():
    return render_template('home.html')

# Endpoint to capture and log the UTK
@app.route('/capture-utk', methods=['POST'])
def capture_utk():
    data = request.json
    hubspot_utk = data.get('hubspotutk')
    if hubspot_utk:
        print(f"Captured HubSpot UTK: {hubspot_utk}")
        # Track the event
        print(track_page_visited(hubspot_utk, '/capture-utk'))

        return jsonify({"message": "UTK received", "hubspot_utk": hubspot_utk}), 200
    else:
        return jsonify({"error": "UTK not found"}), 400
    

# Route for the email form
@app.route('/email-form', methods=['GET', 'POST'])
def email_form():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        id = random_string(32)
        # Identify the user
        analytics.identify(id, {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'created_at': datetime.datetime.now()
        })
        # Redirect to success page with the email as a query parameter
        return redirect(url_for('success', email=email))
    return render_template('email_form.html')

# Route for the success page
@app.route('/success')
def success():
    email = request.args.get('email')
    return render_template('success.html', email=email)

# Endpoint to handle anonymous events
@app.route('/capture-event', methods=['POST'])
def capture_event():
    data = request.json
    hubspot_utk = data.get('hubspotutk')
    button_name = data.get('button_name')
    if hubspot_utk and button_name:
        print(f"Anonymous Event Captured: Button - {button_name}, UTK - {hubspot_utk}")
        # Track the event
        print(track_event(hubspot_utk, "button_clicked", {"button_name": button_name}))

        return jsonify({"message": "Event received", "hubspot_utk": hubspot_utk, "button_name": button_name}), 200
    else:
        return jsonify({"error": "UTK or Button Name not provided"}), 400


if __name__ == '__main__':
    app.run(debug=True)
