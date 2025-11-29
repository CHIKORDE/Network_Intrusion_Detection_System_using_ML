# Network_Intrusion_Detection_System_using_ML

📡 Network Intrusion Detection System (NIDS) using Machine Learning (SVM)

A Machine Learning–based Intrusion Detection System (IDS) designed to identify network attacks and anomalies using the Support Vector Machine (SVM) algorithm.
This project includes data preprocessing, feature extraction, model training, and a Flask-based web interface for real-time intrusion detection.

🚀 Features

🔐 Detects normal vs malicious traffic

🧠 SVM classifier trained on NSL-KDD / KDD99 dataset

🧹 Preprocessing & feature extraction pipeline

🌐 Web dashboard built with Flask

📊 User-friendly interface to upload samples & view predictions

⚡ Fast model inference

🛠️ Modular, easy-to-customize project structure

🏗️ Project Architecture
User → Web UI (Flask) → Preprocessing → Trained SVM Model → Prediction → Output (Normal/Attack)

📁 Project Structure
|-- dataset/
|-- models/
|-- static/
|-- templates/
|-- app.py
|-- preprocessing.py
|-- train_model.py
|-- README.md

📊 Dataset

This project uses NSL-KDD / KDD99 dataset.

Dataset Includes:

41 input features

Attack categories: DoS, Probe, R2L, U2R

Binary classification labels (normal/attack)

⚙️ Installation
1. Clone the repository
git clone https://github.com/your-username/NIDS-ML-SVM.git
cd NIDS-ML-SVM

2. Install dependencies
pip install -r requirements.txt

3. Train the model (optional)
python train_model.py

4. Run the web app
python app.py

🧠 Machine Learning Model
Algorithm Used: Support Vector Machine (SVM)

Chosen because:

Works well with high-dimensional network data

Strong generalization & accuracy

Efficient at binary classification (normal vs attack)

Robust to noisy features

🔬 Preprocessing Steps

Handling missing values

Normalization (MinMaxScaler / StandardScaler)

Encoding categorical features

Splitting into train-test

Feature selection

🌐 Web Application
User Can:

Upload a network record (CSV or input fields)

View classification output:

✔️ Normal

❌ Intrusion detected

Check logs and predictions

📦 Technologies Used
Machine Learning

Python

Scikit-learn (SVM, preprocessing)

Pandas, NumPy

Web

Flask

HTML + CSS + Bootstrap

JavaScript

Tools

Jupyter Notebook

VS Code / PyCharm

📌 Future Improvements

Add deep learning models (LSTM, CNN)

Real-time packet capture using Scapy

Multi-class attack classification

Admin dashboard for monitoring

📝 Author

Shrinivas Bharat Chikorde
MCA Graduate | Data Analytics & Cybersecurity Enthusiast
