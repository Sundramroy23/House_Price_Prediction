from flask import Flask, render_template, redirect, url_for, session, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import bcrypt
from flask_sqlalchemy import SQLAlchemy
import pickle
import json
import pandas as pd
import numpy as np

# Initialize the Flask application
app = Flask(__name__)

# Configuration for SQLAlchemy database and secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # URI for SQLite database
app.config['SECRET_KEY'] = 'SundramKumarRoy'  # Secret key for session management

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define the User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key for each user
    name = db.Column(db.String(80), nullable=False)  # User's name
    email = db.Column(db.String(80), unique=True, nullable=False)  # User's unique email
    password = db.Column(db.String(100), nullable=False)  # User's hashed password

    # Constructor to initialize the User object
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Hash the password

    # Method to check if the provided password matches the stored hash
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

# Create all database tables if they do not exist
with app.app_context():
    db.create_all()

# Load machine learning model and location mappings
try:
    model = pickle.load(open('model.pkl', 'rb'))  # Load model from pickle file
    print("Model loaded successfully")
except FileNotFoundError:
    print("Error: model.pkl file not found")
    model = None

try:
    with open('area_key.json') as f:
        locations = json.load(f)  # Load location mappings from JSON file
except FileNotFoundError:
    print("Error: area_key.json file not found")
    locations = {}

# Define the LoginForm using Flask-WTF
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "Enter email"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)], render_kw={"placeholder": "Enter password"})
    submit = SubmitField('Login')
    register = SubmitField('Register')

# Define the RegisterForm using Flask-WTF
class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Route for the login page and user registration
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Create a new instance of LoginForm
    if form.validate_on_submit():  # Check if the form is submitted and valid
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()  # Retrieve user by email

        if user and user.check_password(password):  # Validate the user
            session['email'] = user.email  # Store email in session
            return redirect(url_for('home'))  # Redirect to the home page
        else:
            return render_template('login.html', form=form, error='Invalid email or password')  # Display error message if invalid

    return render_template('login.html', form=form)  # Render the login template

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()  # Create a new instance of RegisterForm
    if form.validate_on_submit():  # Check if the form is submitted and valid
        name = form.name.data
        email = form.email.data
        password = form.password.data

        new_user = User(name=name, email=email, password=password)  # Create a new user
        db.session.add(new_user)  # Add the user to the database
        db.session.commit()  # Commit the transaction

        return redirect(url_for('login'))  # Redirect to the login page after registration

    return render_template('register.html', form=form)  # Render the registration template

# Route for the home page after successful login
@app.route('/home')
def home():
    if 'email' in session:  # Check if the user is logged in
        return render_template('home.html', locations=locations)  # Render the home page
    else:
        return redirect(url_for('login'))  # Redirect to the login page if not logged in

# Route for predicting house prices
@app.route('/predict', methods=['POST'])
def predict():
    if model is None:  # Check if the model is loaded
        return "Model not loaded correctly.", 500

    try:
        # Retrieve and process input data from the form
        location = request.form.get('location')
        area = float(request.form.get('area'))
        bhk = int(request.form.get('bhk'))
        new_togg = request.form.get('toggle')
        gym_tog = request.form.get('gym')
        indoor_tog = request.form.get('ind')
        club_togg = request.form.get('club')
        swimming_tog = request.form.get('swim')

        # Map location to its value
        location_value = locations.get(location, 0)
        new = 1 if new_togg == 'on' else 0
        gym = 1 if gym_tog == 'on' else 0
        indoor = 1 if indoor_tog == 'on' else 0
        club = 1 if club_togg == 'on' else 0
        swimming = 1 if swimming_tog == 'on' else 0

        # Create DataFrame for model input
        input_data = pd.DataFrame([[area, location_value, bhk, new, indoor, gym, club, swimming]],
                                  columns=['Area', 'Location', 'No. of Bedrooms', 'New/Resale', 'Indoor Games', 'Gymnasium', 'Clubhouse', 'Swimming Pool'])

        # Make prediction
        pred = model.predict(input_data)[0] * 1e6  # Convert prediction to a meaningful value
        predicted_price = str(np.round(pred, 2))  # Round the result

        return predicted_price
    except Exception as e:
        return f"An error occurred: {str(e)}", 500  # Return an error message if an exception occurs

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True, port=5000)  # Start the application in debug mode on port 5000
