import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

# 1️⃣ Load CSV
df = pd.read_csv("data/fake_reviews.csv")

# 2️⃣ Basic cleaning
df = df[['review', 'label']].dropna()

# 3️⃣ Split
X_train, X_test, y_train, y_test = train_test_split(
    df['review'], df['label'], test_size=0.2, random_state=42
)

# 4️⃣ Vectorize
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)

# 5️⃣ Train Model
model = LogisticRegression()
model.fit(X_train_vec, y_train)

# 6️⃣ Save model + vectorizer
joblib.dump(model, "fake_review_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("🎉 Model trained and saved!")