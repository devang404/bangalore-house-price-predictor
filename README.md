# 🏠 Bangalore House Price Predictor

A machine learning-based web application that estimates house prices in Bangalore using user-provided details such as BHK, square footage, bathrooms, location, and more. Built with Flask and powered by a trained Random Forest model.

## 🚀 Features

- 📍 Location-based price prediction using actual Bangalore housing data
- 🧠 Trained ML model using scikit-learn
- 📊 Visualizations for price trends
- 🌐 Simple and interactive web UI
- 🧩 Modular Python scripts for data handling and preprocessing

## 📂 Project Structure

```
/bangalore-house-price-predictor
│
├── data/               # Raw and processed CSV datasets
├── models/             # Trained ML models and scalers
├── database/           # SQLite database files
├── static/             # CSS and JS files
├── templates/          # HTML templates for frontend
├── scripts/            # Scripts for database setup and data extraction
├── app.py              # Flask app entry point
├── main.py             # Model prediction logic
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
```

## 🧪 How to Run Locally

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/bangalore-house-price-predictor.git
cd bangalore-house-price-predictor
```

### 2. Create a virtual environment (optional)

```bash
python -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate     # For Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Access the app at `http://127.0.0.1:5000/`

## 💼 Technologies Used

- Python
- Flask
- Scikit-learn
- SQLite
- HTML/CSS/JS (Frontend)

## 📈 Model Info

- Model Type: RandomForestRegressor
- Trained with features: BHK, Bath, Total Sqft, Property Age, Location
- Feature Engineering: One-hot encoding, scaling, etc.



## 📄 License

MIT License
