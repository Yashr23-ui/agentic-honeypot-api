import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle
import os

DATA_PATH = "ml/data/spam.csv"

# Load dataset
data = pd.read_csv(DATA_PATH, encoding="latin-1")
data = data[["v1", "v2"]]
data.columns = ["label", "text"]

# Map labels: spam -> scam (1), ham -> normal (0)
data["label"] = data["label"].map({"spam": 1, "ham": 0})

X = data["text"]
y = data["label"]

# TF-IDF Vectorizer
vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2)
)

X_vec = vectorizer.fit_transform(X)

# Logistic Regression model
model = LogisticRegression(max_iter=1000)
model.fit(X_vec, y)

# Ensure ml directory exists
os.makedirs("ml", exist_ok=True)

# Save model and vectorizer separately
with open("ml/scam_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("ml/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print(" Model and vectorizer saved successfully")
