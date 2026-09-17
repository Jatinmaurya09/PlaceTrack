import os
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix)

DATA_PATH = "dataset/student_placement.csv"
MODEL_PATH = "model/placement_model.pkl"

os.makedirs("dataset", exist_ok=True)
os.makedirs("model", exist_ok=True)

# ---------- Auto-generate demo data if CSV missing ----------
if not os.path.exists(DATA_PATH) or os.path.getsize(DATA_PATH) == 0:
    np.random.seed(42)
    n = 800
    df = pd.DataFrame({
        "age": np.random.randint(18, 31, n),
        "gender": np.random.choice(["Male", "Female", "Other"], n),
        "branch": np.random.choice(["CSE", "IT", "AI-ML", "ECE", "Mechanical", "Civil", "Other"], n),
        "cgpa": np.round(np.random.uniform(5.0, 10.0, n), 2),
        "tenth_percentage": np.round(np.random.uniform(55, 99, n), 2),
        "twelfth_percentage": np.round(np.random.uniform(50, 98, n), 2),
        "backlogs": np.random.choice([0, 0, 0, 1, 1, 2, 3], n),
        "attendance_percentage": np.round(np.random.uniform(50, 100, n), 2),
        "internship_experience": np.random.choice(["Yes", "No"], n),
        "dsa_level": np.random.choice(["Beginner", "Intermediate", "Advanced"], n),
        "coding_practice": np.random.choice(["None", "Occasionally", "Regularly"], n),
        "projects_completed": np.random.randint(0, 11, n),
        "aptitude_level": np.random.choice(["Not Started", "Basic", "Good"], n),
        "communication_level": np.random.choice(["Weak", "Average", "Good"], n),
        "mock_interviews": np.random.randint(0, 21, n),
    })
    score = (
        df["cgpa"] * 8
        + (df["internship_experience"] == "Yes") * 8
        + df["dsa_level"].map({"Beginner": 0, "Intermediate": 5, "Advanced": 10})
        + df["coding_practice"].map({"None": 0, "Occasionally": 3, "Regularly": 7})
        + df["projects_completed"] * 1.5
        + df["aptitude_level"].map({"Not Started": 0, "Basic": 3, "Good": 6})
        + df["communication_level"].map({"Weak": 0, "Average": 3, "Good": 6})
        + df["mock_interviews"] * 0.8
        - df["backlogs"] * 5
        + np.random.normal(0, 6, n)
    )
    df["placement_status"] = np.where(score >= np.percentile(score, 45),
                                       "Placed", "Not Placed")
    df.to_csv(DATA_PATH, index=False)
    print("Demo dataset created at:", DATA_PATH)

# ---------- Load ----------
df = pd.read_csv(DATA_PATH)
print("Dataset shape:", df.shape)

# IMPORTANT: gender is EXCLUDED from features (fairness)
DROP_FEATURES = ["gender", "placement_status"]
FEATURES = [c for c in df.columns if c not in DROP_FEATURES]

X = df[FEATURES]
y = df["placement_status"]

num_features = ["age", "cgpa", "tenth_percentage", "twelfth_percentage",
                "backlogs", "attendance_percentage", "projects_completed",
                "mock_interviews"]
cat_features = [c for c in FEATURES if c not in num_features]

preprocessor = ColumnTransformer([
    ("num", StandardScaler(), num_features),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
])

# ---------- Split ----------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ---------- Compare models ----------
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Decision Tree": DecisionTreeClassifier(random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
}

best_name, best_acc, best_pipe = "", 0, None
for name, clf in models.items():
    pipe = Pipeline([("prep", preprocessor), ("clf", clf)])
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"\n--- {name} ---")
    print(f"  Accuracy : {acc:.4f}")
    print(f"  Precision: {precision_score(y_test, preds, pos_label='Placed'):.4f}")
    print(f"  Recall   : {recall_score(y_test, preds, pos_label='Placed'):.4f}")
    print(f"  F1-score : {f1_score(y_test, preds, pos_label='Placed'):.4f}")
    print(f"  Confusion Matrix:\n{confusion_matrix(y_test, preds)}")
    if acc > best_acc:
        best_acc, best_name, best_pipe = acc, name, pipe

print(f"\nBEST MODEL: {best_name} (Accuracy: {best_acc:.4f})")

joblib.dump({
    "pipeline": best_pipe,
    "features": FEATURES,
    "num_features": num_features,
    "cat_features": cat_features,
    "model_name": best_name,
    "accuracy": best_acc,
}, MODEL_PATH)
print("Model saved at:", MODEL_PATH)