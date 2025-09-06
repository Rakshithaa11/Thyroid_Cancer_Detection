This project is a Flask web application that allows doctors to register/login, manage patients, and predict thyroid disease using lab test results (TSH, T3, T4) along with patient symptoms. Predictions are stored in a MySQL database (via XAMPP).

Prerequisites:
Python 3.8+
XAMPP (MySQL + Apache)
pip (Python package manager)

Step 1: Install XAMPP & Start MySQL
Download and install XAMPP from apachefriends.org
Open the XAMPP Control Panel → Start Apache and MySQL.
Open phpMyAdmin in your browser.

Step 2: Create Database and Tables
1.In phpMyAdmin, click Databases → Create new database → name it:
thyroid_model

2.Run the following SQL scripts to create required tables:

-- Users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    role ENUM('doctor','patient') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patients Table
CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    full_name VARCHAR(100),
    age INT,
    gender VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Thyroid Predictions Table
CREATE TABLE thyroid_predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NULL,
    name VARCHAR(100),
    age INT,
    gender VARCHAR(20),
    tsh FLOAT,
    t3 FLOAT,
    t4 FLOAT,
    symptom TEXT,
    result VARCHAR(50),
    predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);

To Run the Flask App
python app.py


    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);
