import joblib
import numpy as np

# Load the model once when the module is imported
model = joblib.load("thyroid_model.pkl")

def predict_thyroid(tsh, t3, t4):
    """
    Predict thyroid condition based on TSH, T3, and T4 values.
    Returns:
        result_label: "Malignant" or "Benign"
    """
    # Ensure inputs are floats
    features = np.array([[float(tsh), float(t3), float(t4)]])

    # Predict
    prediction = model.predict(features)[0]

    # Predict probability if available
    probability = None
    if hasattr(model, "predict_proba"):
        probability = round(model.predict_proba(features).max() * 100, 2)

    # Ensure label is string (as per training)
    if isinstance(prediction, (np.int64, int)):
        if prediction == 1:
            result_label = "Malignant"
        else:
            result_label = "Benign"
    else:
        result_label = str(prediction)

    # ✅ Return only the label (string), not a tuple
    return result_label