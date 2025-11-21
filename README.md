
🏠Bangalore House Price Predictor

This project implements a complete end-to-end data science pipeline: from data preprocessing and training a predictive model to deploying it as a functional, interactive web application.

The core goal is to provide a reliable estimate of house prices in various localities of Bangalore (the "Silicon Valley of India") by utilizing a machine learning Random Forest Regressor model. The predictions are served via a Flask backend, allowing users to input property details like location, total square footage, and the number of bedrooms (BHK).
## ✨Features

- Real-time Prediction: Get instant house price predictions based on user inputs.
- Interactive Web Interface: A user-friendly front-end built with HTML, CSS, and JavaScript.
- Location Awareness: Supports a wide range of localities within Bangalore.
- ML Model Backend: Utilizes a trained Random Forest Regression model for accurate estimates.


## 🛠️ Technology Stack

**Backend Framework:** Python, Flask

**Frontend:** HTML,CSS,JavaScript

**Machine Learning:** Scikit-learn (sklearn)

**Data Handling:** Pandas,Numpy

**Database:** SQLite


## 📁 Project Structure

```
bangalore-house-price-predictor/
├── app.py                     → Flask web application (serves predictions)
├── requirements.txt           → List of all required Python packages
├── columns.json               → Stores feature/column names (including locations)
├── model.pkl                  → Trained machine learning model file
├── main.py                    → Script for preprocessing and training the model
├── main_new.py                → Updated version of the training script
├── init_db.py                 → Initializes the SQLite database
├── insert_locations.py        → Inserts location names into the database
├── templates/                 → HTML template files
│   └── index.html             → Main UI page for predictions
└── static/                    → Static assets (CSS, JS)
    ├── css/                   → Stylesheets
    └── js/                    → JavaScript files
```


## 🚀Installation

---

## ✅ Prerequisites

- Python 3.x  
- Git

---

## 🔹 Step 1: Clone the Repository

```
git clone https://github.com/devang404/bangalore-house-price-predictor.git
cd bangalore-house-price-predictor
```

---

## 🔹 Step 2: Create and Activate Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

```
# Create environment
python -m venv venv
```

Activate it:

**Windows**
```
.\venv\Scripts\activate
```

**macOS/Linux**
```
source venv/bin/activate
```

---

## 🔹 Step 3: Install Dependencies

```
pip install -r requirements.txt
```

---

## 🔹 Step 4: Run Database Initialization (if applicable)

If your application uses a database for locations, initialize it:

```
python init_db.py
python insert_locations.py
```

(Optional)
```
python main.py
```

---

## 🔹 Step 5: Run the Flask Application

```
python app.py
```

Your application will run locally at:

```
http://127.0.0.1:5000/
```

---
## 👨‍💻 Usage



- Open your browser and go to the local server address.  
- You will see an input form.  
- Select a **Location** (dropdown).  
- Enter **Total Square Feet**.  
- Enter **BHK** (e.g., 2 or 3).  
- Click **Predict Price**.  
- The predicted price (in lakhs) will be displayed.
- Check nearby amenities by clicling on buttons provided(school,hsopital,etc)

---

## 📊 Data & Model Details

### **Data**
The model is trained on Bangalore property listing data.  
Key features include:

- Location  
- Total Square Feet  
- BHK  

### **Model**
- Algorithm: **Random Forest Regression**  
- Trained using error minimization techniques like **MSE/RMSE**  
- The trained model file is loaded in `app.py` to serve predictions  

---

## 📷Screenshots


### Home Page
![Home Page](https://github.com/devang404/bangalore-house-price-predictor/blob/main/Screenshot%202025-11-05%20024151.png)

![Nearby Amenities](https://github.com/devang404/bangalore-house-price-predictor/blob/main/Screenshot%202025-11-05%20024320.png)
