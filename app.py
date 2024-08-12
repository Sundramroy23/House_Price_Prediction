from flask import Flask, render_template, request
import pickle
import json
import pandas as pd
import numpy as np

app = Flask(__name__)

# Load the model and locations file
try:
    model = pickle.load(open('model.pkl', 'rb'))
    print("Model loaded successfully")
except FileNotFoundError:
    print("Error: model.pkl file not found")
    model = None

try:
    with open('area_key.json') as f:
        locations = json.load(f)
except FileNotFoundError:
    print("Error: area_key.json file not found")
    locations = {}

@app.route('/')
def home():
    return render_template('home.html', locations=locations)

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return "Model not loaded correctly.", 500

    try:
        location = request.form.get('location')
        area = float(request.form.get('area'))
        bhk = int(request.form.get('bhk'))
        new_togg = request.form.get('toggle')
        gym_tog = request.form.get('gym')
        indoor_tog = request.form.get('ind')
        club_togg = request.form.get('club')
        swimming_tog = request.form.get('swim')

        location_value = locations.get(location, 0)
        new = 1 if new_togg == 'on' else 0
        gym = 1 if gym_tog == 'on' else 0
        indoor = 1 if indoor_tog == 'on' else 0
        club = 1 if club_togg == 'on' else 0
        swimming = 1 if swimming_tog == 'on' else 0

        input_data = pd.DataFrame([[area, location_value, bhk, new, indoor, gym, club, swimming]],
                                  columns=['Area', 'Location', 'No. of Bedrooms', 'New/Resale', 'Indoor Games', 'Gymnasium', 'Clubhouse', 'Swimming Pool'])

        pred = model.predict(input_data)[0] * 1e6
        predicted_price = str(np.round(pred, 2))

        return predicted_price
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
