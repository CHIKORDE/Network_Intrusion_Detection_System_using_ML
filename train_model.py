import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import f1_score
import joblib
import os

# Load data
df = pd.read_csv("CICIDS2017_sample.csv")
df.replace([float('inf'), -float('inf')], pd.NA, inplace=True)
df.dropna(inplace=True)

# Define features
features = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Fwd IAT Mean",
    "Bwd IAT Mean",
    "SYN Flag Count"
]

X = df[features]
y = df['Label']

# Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)
joblib.dump(le, "model/label_encoder.pkl")

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, "model/preprocessor.pkl")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)

# Train SVM
clf = SVC(kernel='rbf', C=1, gamma='scale')
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
f1 = f1_score(y_test, y_pred, average='weighted')
print(f"F1-Score (Weighted): {f1:.4f}")

# Save model
joblib.dump(clf, "model/nids_model.pkl")