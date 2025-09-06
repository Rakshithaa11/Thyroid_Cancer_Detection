import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# === 1. Load CSV ===
df = pd.read_csv("thyroid_cancer_dataset_10000.csv")  # Change filename if needed

# Normalize column names (lowercase + remove spaces)
df.columns = df.columns.str.strip().str.lower()

# Try to find correct column names for features
required_cols = ["tsh", "t3", "t4"]
for col in required_cols:
    if col not in df.columns:
        raise KeyError(f"Column '{col}' not found in CSV. Found columns: {list(df.columns)}")

# === 2. Select features & target ===
X = df[required_cols]
# Try to find the target column automatically
possible_targets = ["target", "label", "class", "diagnosis", "result"]
target_col = None
for t in possible_targets:
    if t in df.columns:
        target_col = t
        break

if not target_col:
    raise KeyError(f"No target column found. Expected one of {possible_targets}")

y = df[target_col]

# === 3. Train-Test Split ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === 4. Train RandomForest Model ===
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# === 5. Evaluate ===
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {acc * 100:.2f}%")

# === 6. Save Model ===
with open("thyroid_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model saved as 'thyroid_model.pkl'")
