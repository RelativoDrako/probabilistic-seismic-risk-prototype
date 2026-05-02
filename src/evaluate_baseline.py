"""
Evaluate baseline models
"""
import joblib
import tensorflow as tf
from preprocessing import sliding_window, normalize_signal, load_signal
from sklearn.metrics import classification_report
import numpy as np

signal = load_signal()
signal_norm = normalize_signal(signal)
windows = sliding_window(signal_norm, window_size=50, step=10)
labels = np.zeros(len(windows))
labels[len(windows)//2:] = 1

X_test = windows
y_test = labels

# Logistic Regression
lr_model = joblib.load("models/baseline/logistic_regression.pkl")
X_test_lr = X_test.reshape(X_test.shape[0], -1)
y_pred_lr = lr_model.predict(X_test_lr)
print("=== Logistic Regression Evaluation ===")
print(classification_report(y_test, y_pred_lr))

# CNN Ligera
cnn_model = tf.keras.models.load_model("models/baseline/cnn_light.h5")
X_test_cnn = X_test[..., np.newaxis]
eval_cnn = cnn_model.evaluate(X_test_cnn, y_test, verbose=0)
print(f"=== CNN Ligera Evaluation ===\nLoss: {eval_cnn[0]:.4f}, Accuracy: {eval_cnn[1]*100:.2f}%")
