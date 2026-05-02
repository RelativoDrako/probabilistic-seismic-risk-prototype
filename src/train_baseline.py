"""
Train baseline models: Logistic Regression and lightweight CNN
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv1D, Flatten, Input
import os

# ---------- Load data ----------
from preprocessing import sliding_window, normalize_signal, load_signal

signal = load_signal()
signal_norm = normalize_signal(signal)
windows = sliding_window(signal_norm, window_size=50, step=10)

# Create labels: simulate event start at middle
labels = np.zeros(len(windows))
labels[len(windows)//2:] = 1

X_train, X_test, y_train, y_test = train_test_split(windows, labels, test_size=0.2, random_state=42)

# ---------------- Logistic Regression ----------------
X_train_lr = X_train.reshape(X_train.shape[0], -1)
X_test_lr = X_test.reshape(X_test.shape[0], -1)

lr_model = LogisticRegression(max_iter=500)
lr_model.fit(X_train_lr, y_train)
y_pred_lr = lr_model.predict(X_test_lr)

print("=== Logistic Regression Baseline ===")
print(classification_report(y_test, y_pred_lr))

os.makedirs("models/baseline", exist_ok=True)
import joblib
joblib.dump(lr_model, "models/baseline/logistic_regression.pkl")

# ---------------- CNN Ligera ----------------
X_train_cnn = X_train[..., np.newaxis]  # add channel
X_test_cnn = X_test[..., np.newaxis]

cnn_model = Sequential([
    Input(shape=(50,1)),
    Conv1D(8, kernel_size=5, activation="relu"),
    Flatten(),
    Dense(1, activation="sigmoid")
])
cnn_model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
cnn_model.fit(X_train_cnn, y_train, epochs=10, batch_size=16, verbose=0)

cnn_model.evaluate(X_test_cnn, y_test)
cnn_model.save("models/baseline/cnn_light.h5")
print("Modelos baseline guardados en models/baseline/")
