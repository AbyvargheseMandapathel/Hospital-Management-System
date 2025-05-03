import numpy as np
import pandas as pd
import joblib  # Import joblib for saving models
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier

# Load dataset
DATA_PATH = "datasetoutput.csv"
data = pd.read_csv(DATA_PATH).dropna(axis=1)

# Encode target variable
encoder = LabelEncoder()
data["prognosis"] = encoder.fit_transform(data["prognosis"])

# Save the encoder for later use
joblib.dump(encoder, "models/label_encoder.pkl")

# Split data
X = data.iloc[:, :-1]
y = data.iloc[:, -1]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=24)

# Train models
svm_model = SVC(probability=True)
nb_model = GaussianNB()
rf_model = RandomForestClassifier(random_state=18)

svm_model.fit(X_train, y_train)
nb_model.fit(X_train, y_train)
rf_model.fit(X_train, y_train)

# Save trained models
joblib.dump(svm_model, "models/svm_model.pkl")
joblib.dump(nb_model, "models/nb_model.pkl")
joblib.dump(rf_model, "models/rf_model.pkl")

print("Models saved successfully! done")
