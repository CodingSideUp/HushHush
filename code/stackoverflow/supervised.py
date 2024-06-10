import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, accuracy_score, confusion_matrix
from sklearn.svm import SVC
import os
import pickle
from xgboost import XGBClassifier

class StackOverflowPrediction():
    def __init__(self):
        user = "root"
        password = "password"
        host = "localhost"
        db_name = "stackoverflow"

        self.engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{db_name}')
        # Get the directory path of the current Python script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the pickle file using os.path.join
        self.scalerpath = os.path.join(current_dir, 'pickle_files', 'standardScaler.pkl')
        self.xgbpath = os.path.join(current_dir, 'pickle_files', 'xgb_classifier.pkl')
        self.svcpath = os.path.join(current_dir, 'pickle_files', 'svc_classifier.pkl')
        self.adapath = os.path.join(current_dir, 'pickle_files', 'ada_classifier.pkl')
        # self.scalerpath = "pickle_files/standardScaler.pkl"
        self.features = ['reputation', 'accept_rate', 'Bronze_Badge_Count', 'Silver_Badge_Count', 'Gold_Badge_Count', 'Answer_Count', 'Answer_Score', 'Question_Count', 'Question_Score']

        with open(self.scalerpath, 'rb') as f:
            self.scaler = pickle.load(f)

        try:
            with open(self.xgbpath, 'rb') as f:
                self.xgb_classifier = pickle.load(f)
        except:
            self.xgb_classifier = XGBClassifier(random_state = 5)
        
        try:
            with open(self.svcpath, 'rb') as f:
                self.svc_classifier = pickle.load(f)
        except:
            self.svc_classifier = SVC(C = 6.5, kernel = "rbf", gamma = 0.2, random_state = 5)

        try:
            with open(self.adapath, 'rb') as f:
                self.ada_classifier = pickle.load(f)
        except:
            self.ada_classifier = AdaBoostClassifier(n_estimators = 131, learning_rate = 1.5, algorithm = "SAMME.R", random_state = 5)

    def get_training_data(self):
        return pd.read_sql_table(table_name="labelleddata", con=self.engine)
        
    def get_data(self, skill):
        df = pd.read_sql_query(sql=f"SELECT * FROM userdata WHERE Tag_Name = '{skill}'", con=self.engine)
        if df.empty:
            return df
        else:
            df[self.features] = self.scaler.transform(df[self.features])
            return df

    def split_training_data(self, X, y, test_split_size):
        return train_test_split(X, y, test_size=test_split_size, random_state=5)

    def fit(self, X_train, y_train):
        self.xgb_classifier.fit(X_train, y_train)
        self.svc_classifier.fit(X_train, y_train)
        self.ada_classifier.fit(X_train, y_train)

        with open(self.xgbpath, 'wb') as f:
            pickle.dump(self.xgb_classifier, f)
        
        with open(self.svcpath, 'wb') as f:
            pickle.dump(self.svc_classifier, f)

        with open(self.adapath, 'wb') as f:
            pickle.dump(self.ada_classifier, f)

    def predict(self, X_test):
        pred_xgb = self.xgb_classifier.predict(X_test)
        pred_svc = self.svc_classifier.predict(X_test)
        pred_ada = self.ada_classifier.predict(X_test)

        final_pred = np.zeros(len(pred_xgb), dtype = int)
        unique_count = {}

        for i in range(len(pred_xgb)):
            for j in np.unique([pred_xgb, pred_svc, pred_ada]):
                unique_count[j] = 0

            unique_count[pred_xgb[i]] += 1
            unique_count[pred_svc[i]] += 1
            unique_count[pred_ada[i]] += 1

            final_pred[i] = max(unique_count, key = unique_count.get)

        return final_pred

    def metrics(self, y_test, y_pred):
        print(f'Accuracy : {accuracy_score(y_test, y_pred)}')
        print(f'Precision : {precision_score(y_test, y_pred)}')
        print(f'Recall : {recall_score(y_test, y_pred)}')
        print(f'F1 Score : {f1_score(y_test, y_pred)}')
        print(f'Area under ROC Score : {roc_auc_score(y_test, y_pred)}')
        print(f'Confusion Matrix : \n {confusion_matrix(y_test, y_pred)}')

if __name__ == "__main__":
    model = StackOverflowPrediction()
    df = model.get_training_data()
    X_train, X_test, y_train, y_test = model.split_training_data(df[model.features], df.iloc[:, -1], 0.3)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    model.metrics(y_test, y_pred)