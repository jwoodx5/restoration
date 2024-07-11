import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import secrets
import time
import json
from datetime import datetime
import pytz
import re
import smtplib
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from google.oauth2 import service_account
from google.cloud import firestore

# Check if FIREBASE_SERVICE_ACCOUNT environment variable is set
# service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT')
# if service_account_path is None:
#     raise ValueError("FIREBASE_SERVICE_ACCOUNT environment variable not set. Set the environment variable with the path to your service account key.")

# Check if GOOGLE_APPLICATION_CREDENTIALS is set
service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if service_account_path is None:
    raise ValueError(
        "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Set the environment variable with the path to your service account key.")

# Initialize Firebase app with the service account
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
serializer = URLSafeTimedSerializer(app.secret_key)


# Access Firestore
db = firestore.Client()


@app.route('/')
def index():
    return render_template('app.html')
# -----------------------------------------------------------------------------------------------------


@app.route('/login', methods=['POST'])
def login():

    # Get username and password from the form
    entered_username = request.form.get('username')
    entered_password = request.form.get('password')

    # Query Firestore for the entered username
    security_ref = db.collection('security')
    query = security_ref.where(
        'Username', '==', entered_username).where(
        'Password', '==', entered_password).get()

    # Check if a user with the given username and password exists
    login_status = 'success' if query else 'failed'

    # Assuming there's only one document with the given username and password
    # Access the document data
    user_data = query[0].to_dict() if query else None

    if login_status == 'success':
        return redirect(url_for('customer_lookup'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # Assuming you verify the email exists in your system
        token = serializer.dumps(email, salt='email-confirm-salt')
        # send_reset_email(email, token)
        flash(
            'A password reset email has been sent, if the email exists in our system.',
            'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(
            token,
            salt='email-confirm-salt',
            max_age=3600)  # 1 hour expiration
    except SignatureExpired:
        flash(
            'The password reset link is expired. Please try the reset process again.',
            'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        # Here you should update the password in Firestore
        # Example: update_password(email, new_password)
        flash('Your password has been updated.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)
# --------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
@app.route('/customer-lookup', methods=['GET', 'POST'])
def customer_lookup():
    phone_number = None  # Initialize phone_number

    if request.method == 'POST':
        # Handle the form submission logic
        phone_number = request.form.get('phone_number')
        # Remove whitespace, commas, hyphens, and spaces
        phone_number = re.sub(r'[\s,-]|[\(\)]', '', phone_number)

        customers_ref = db.collection('customers')
        query = customers_ref.where('phone_number', '==', phone_number).get()

        lookup_status = 'success' if query else 'failed'
        customer_data = query[0].to_dict() if query else None

        if lookup_status == 'success':
            return redirect(
                url_for(
                    'customer_page',
                    customer_data=json.dumps(customer_data),
                    phone_number=phone_number))

    # Render the customer lookup page for GET requests
    return render_template('customer_lookup.html', phone_number=phone_number)

# ----------------------------------------------------------------------------------------------------------


@app.route('/new-customers', methods=['GET', 'POST'])
def new_customers():
    if request.method == 'POST':
        # Initialize error_messages list
        error_messages = []

        # Get form data from the submitted form
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        address = request.form.get('address')
        zip_code = request.form.get('zip_code')
        state = request.form.get('state')
        phone_number = re.sub(
            r'[\s,-]|[\(\)]',
            '',
            request.form.get('phone_number'))
        email = request.form.get('email')

        # Validate Email: Must contain @ symbol
        if '@' not in email:
            error_messages.append("Email must contain an @ symbol.")

        # Check for any validation errors
        if error_messages:
            # Combine all error messages into one flash message or handle
            # individually
            for message in error_messages:
                flash(message, 'error')
            # Return to the form with error messages
            return render_template('new_customers.html')

        # Proceed if no errors
        try:
            # Assuming you have a 'customers' collection in Firestore
            customers_ref = db.collection('customers')

            # Add a new document with the provided data
            customers_ref.add({
                'Fname': fname,
                'Lname': lname,
                'Address': address,
                'Zip_Code': zip_code,
                'State': state,
                'phone_number': phone_number,
                'email': email
            })

            flash('Customer successfully added', 'success')
            return redirect(url_for('customer_page', customer_data=json.dumps({
                'Fname': fname,
                'Lname': lname,
                'Address': address,
                'Zip_Code': zip_code,
                'State': state,
                'phone_number': phone_number,
                'email': email
            })))
        except Exception as e:
            print(f"Error inserting into Firestore: {e}")
            flash('Failed to add customer', 'error')

    # Render the form for GET requests
    return render_template('new_customers.html')
# -------------------------------------------------------------------------------------------------


@app.route('/customer-page')
def customer_page():
    # Clear the 'submitted' session flag to allow new submissions
    session.pop('submitted', None)

    customer_data_str = request.args.get('customer_data', None)

    if customer_data_str:
        try:
            # Assuming customer_data_str is a valid JSON string
            customer_data = json.loads(customer_data_str)

            # Additional logic for rendering the customer_page.html template
            # with the provided customer_data
            return render_template(
                'customer_page.html',
                customer_data=customer_data)
        except json.JSONDecodeError:
            flash('Invalid customer data format', 'error')
            # Consider redirecting to a more general page if customer data is invalid
            # Or render the same page with an error message
            return render_template('customer_lookup.html', error='Invalid customer data format')

    # If customer_data_str is not provided, flash an error and redirect to the customer lookup page
    # or render customer_lookup.html directly with an error message
    flash('Customer data not found', 'error')
    return render_template('customer_lookup.html', error='Customer data not found')

# ---------------------------------------------------------------------------------------------------
def get_customer_data(phone_number):
    customer_query = db.collection('customers').where('phone_number', '==', phone_number).limit(1).get()
    if customer_query:
        return customer_query[0].to_dict()
    else:
        # Return an empty dictionary if no customer is found
        return {}
# -------------------------------------------------------------------------------------------------------
    
@app.route('/fire_readings/<phone_number>', methods=['GET', 'POST'])
def fire_readings(phone_number):
    # Ensure the customer exists in the database
    customer_query = db.collection('customers').where('phone_number', '==', phone_number).limit(1).get()
    if not customer_query:
        flash('Customer not found', 'error')
        return redirect(url_for('customer_lookup'))

    customer_ref = customer_query[0].reference
    colorado_timezone = pytz.timezone('America/Denver')

    if request.method == 'POST':
        readings = {
            'Outside': {
                'Temp': request.form.get('outside_temp'),
                'RH': request.form.get('outside_rh'),
                'Note': request.form.get('outside_note'),
                'Date/Time': datetime.now(colorado_timezone)
            },
            'Unaffected': {
                'Temp': request.form.get('unaffected_temp'),
                'RH': request.form.get('unaffected_rh'),
            },
            'Chambers': {}
        }

        # # Process chambers and rooms
        # for key in request.form:
        #     key_parts = key.split('_', 2)
        #     if len(key_parts) == 3 and key_parts[0] == 'chamber':
        #         chamber_name_raw, room_and_reading = key_parts[1], key_parts[2]
        #         chamber_name = chamber_name_raw.replace('_', ' ')
        #         room_name_raw, reading_type = room_and_reading.rsplit('_', 1)
        #         room_name = room_name_raw.replace('_', ' ')

        #         if chamber_name not in readings['Chambers']:
        #             readings['Chambers'][chamber_name] = {}
        #         if room_name not in readings['Chambers'][chamber_name]:
        #             readings['Chambers'][chamber_name][room_name] = {}

        #         readings['Chambers'][chamber_name][room_name][reading_type] = request.form[key]

        # Save to Firestore
        try:
            today_date = datetime.now().strftime('%Y-%m-%d')
            readings_ref = customer_ref.collection('readings').document(today_date)
            readings_ref.set(readings, merge=True)
            flash('Readings submitted successfully!', 'success')
        except Exception as e:
            flash(f'Failed to submit readings: {str(e)}', 'error')

        return redirect(url_for('fire_readings', phone_number=phone_number))

    return render_template('customer_page.html', phone_number=phone_number, customer_data=customer_query[0].to_dict())
# ------------------------------------------------------------------------------------------------------------
def get_customer_data(phone_number):
    customer_query = db.collection('customers').where('phone_number', '==', phone_number).limit(1).get()
    if customer_query:
        # Convert the DocumentSnapshot to a dict and return it
        return customer_query[0].to_dict()
    else:
        # Return an empty dictionary if no customer is found
        return {}

# ---------------------------------------------------------------------------------------------------------------------------------------


@app.route('/water_readings/<phone_number>', methods=['GET', 'POST'])
def water_readings(phone_number):

    if request.method == 'POST':
        reading_1 = request.form.get('water_reading_1')
        reading_2 = request.form.get('water_reading_2')
        reading_3 = request.form.get('water_reading_3')

        try:
            customer_query = db.collection('customers').where(
                'phone_number', '==', phone_number).limit(1).get()

            if customer_query:
                customer_ref = customer_query[0].reference
                readings_ref = customer_ref.collection('water_readings')

                readings_data = {
                    'reading_1': reading_1,
                    'reading_2': reading_2,
                    'reading_3': reading_3
                }

                readings_ref.add(readings_data)

                print("Form submitted successfully!")

                flash('Readings submitted successfully!', 'success')
            else:
                flash('Customer not found', 'error')

        except Exception as e:
            print(f"Error handling readings: {e}")
            flash('Failed to submit readings', 'error')

    return render_template('water_readings.html', phone_number=phone_number)

# Render the form template on GET request
    #return render_template('fire_readings.html', phone_number=phone_number)

# ---------------------------------------------------------------------------------------------------------------------------------


@app.route('/mold_readings/<phone_number>', methods=['GET', 'POST'])
def mold_readings(phone_number):

    if request.method == 'POST':
        reading_1 = request.form.get('mold_reading_1')
        reading_2 = request.form.get('mold_reading_2')
        reading_3 = request.form.get('mold_reading_3')

        try:
            customer_query = db.collection('customers').where(
                'phone_number', '==', phone_number).limit(1).get()

            if customer_query:
                customer_ref = customer_query[0].reference
                readings_ref = customer_ref.collection('mold_readings')

                readings_data = {
                    'reading_1': reading_1,
                    'reading_2': reading_2,
                    'reading_3': reading_3
                }

                readings_ref.add(readings_data)

                print("Form submitted successfully!")

                flash('Readings submitted successfully!', 'success')
            else:
                flash('Customer not found', 'error')

        except Exception as e:
            print(f"Error handling readings: {e}")
            flash('Failed to submit readings', 'error')

    return render_template('mold_readings.html', phone_number=phone_number)

# ----------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
