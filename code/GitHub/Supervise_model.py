import os
import pandas as pd
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle

from xgboost import XGBClassifier

def return_models():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, 'pickel file\\scaler.pkl'), 'rb') as scaler_file:
        scaler = pickle.load(scaler_file)

    with open(os.path.join(current_dir, 'pickel file\\rf_model.pkl'), 'rb') as rf_model_file:
        rf_classifier = pickle.load(rf_model_file)

    with open(os.path.join(current_dir, 'pickel file\\ada_model.pkl'), 'rb') as ada_model_file:
        ada_classifier = pickle.load(ada_model_file)
    
    with open(os.path.join(current_dir, 'pickel file\\xgb_model.pkl'), 'rb') as xgb_model_file:
        xgb_classifier = pickle.load(xgb_model_file)
    
    return scaler, rf_classifier, ada_classifier, xgb_classifier
    

def train_test_models(X, y):
    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Standardize features
    try:
        with open(os.path.join(current_dir, 'pickel file\\scaler.pkl'), 'rb') as scaler_file:
            scaler = pickle.load(scaler_file)
            X_train_scaled = scaler.fit_transform(X_train)
    except:
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

    X_test_scaled = scaler.transform(X_test)
    
    # Initialize models
    try:
        with open(os.path.join(current_dir, 'pickel file\\rf_model.pkl'), 'rb') as rf_model_file:
            rf_classifier = pickle.load(rf_model_file)
    except:
        rf_classifier = RandomForestClassifier()
    
    try:
        with open(os.path.join(current_dir, 'pickel file\\ada_model.pkl'), 'rb') as ada_model_file:
            ada_classifier = pickle.load(ada_model_file)
    except:
        ada_classifier = AdaBoostClassifier()
    
    try:
        with open(os.path.join(current_dir, 'pickel file\\xgb_model.pkl'), 'rb') as xgb_model_file:
            xgb_classifier = pickle.load(xgb_model_file)
    except:
        xgb_classifier = XGBClassifier()
    
    # Train models
    rf_classifier.fit(X_train_scaled, y_train)
    ada_classifier.fit(X_train_scaled, y_train)
    xgb_classifier.fit(X_train_scaled, y_train)
    
    # Save scaler and models
    if __name__ == "__main__":
        with open(os.path.join(current_dir, 'pickel file\\scaler.pkl'), 'wb') as scaler_file:
            pickle.dump(scaler, scaler_file)
        with open(os.path.join(current_dir, 'pickel file\\rf_model.pkl'), 'wb') as rf_model_file:
            pickle.dump(rf_classifier, rf_model_file)
        with open(os.path.join(current_dir, 'pickel file\\ada_model.pkl'), 'wb') as ada_model_file:
            pickle.dump(ada_classifier, ada_model_file)
        with open(os.path.join(current_dir, 'pickel file\\xgb_model.pkl'), 'wb') as xgb_model_file:
            pickle.dump(xgb_classifier, xgb_model_file)
    
    # Evaluate models
    rf_metrics = evaluate_model(rf_classifier, X_test_scaled, y_test, "Random Forest")
    ada_metrics = evaluate_model(ada_classifier, X_test_scaled, y_test, "AdaBoost")
    xgb_metrics = evaluate_model(xgb_classifier, X_test_scaled, y_test, "XGBoost")


def evaluate_model(classifier, X_test, y_test, model_name):
    # Calculate metrics
    accuracy = classifier.score(X_test, y_test)
    precision = precision_score(y_test, classifier.predict(X_test))
    recall = recall_score(y_test, classifier.predict(X_test))
    f1 = f1_score(y_test, classifier.predict(X_test))
    roc = roc_auc_score(y_test, classifier.predict(X_test))
    
    # Print metrics
    print(f'Model: {model_name}')
    print(f'Accuracy: {accuracy}')
    print(f'Precision: {precision}')
    print(f'Recall: {recall}')
    print(f'F1 Score: {f1}')
    print(f'Area under ROC Score: {roc}')
    print('')
    
current_dir = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(current_dir, 'label_data_3.csv'))
features = ['Stargazers','Contributors', 'Subscribers', 'Pulls', 'Commits', 'Size', 'Followers','Following']
X = df[features]
y = df.iloc[:,-1]

if __name__ == "__main__":
    train_test_models(X,y)