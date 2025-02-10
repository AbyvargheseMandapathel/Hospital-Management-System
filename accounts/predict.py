import numpy as np
import joblib
import pandas as pd

# Load trained models
svm_model = joblib.load("models/svm_model.pkl")
nb_model = joblib.load("models/nb_model.pkl")
rf_model = joblib.load("models/rf_model.pkl")
encoder = joblib.load("models/label_encoder.pkl")

# Load symptom index mapping
symptoms = list(pd.read_csv("dataset.csv").columns)[:-1]
symptom_index = {symptom: idx for idx, symptom in enumerate(symptoms)}

def predict_disease(user_symptoms):
    input_data = [0] * len(symptom_index)
    
    for symptom in user_symptoms.split(","):
        if symptom in symptom_index:
            input_data[symptom_index[symptom]] = 1

    input_data = np.array(input_data).reshape(1, -1)

    # Predictions
    rf_pred = encoder.inverse_transform([rf_model.predict(input_data)[0]])[0]
    nb_pred = encoder.inverse_transform([nb_model.predict(input_data)[0]])[0]
    svm_pred = encoder.inverse_transform([svm_model.predict(input_data)[0]])[0]

    # Final prediction using mode
    from statistics import mode
    final_prediction = mode([rf_pred, nb_pred, svm_pred])

    return {
        "Random Forest": rf_pred,
        "Naive Bayes": nb_pred,
        "SVM": svm_pred,
        "Final Prediction": final_prediction
    }