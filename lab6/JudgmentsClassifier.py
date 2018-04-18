from sklearn.model_selection import train_test_split
import numpy as np
from sklearn.preprocessing import LabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import svm
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support

class JudgmentsClassifier():

    def __init__(self, X, Y):
        self.__X__ = X
        self.__Y__ = Y
        self.category_list = [
            'sprawy cywilne',
            'sprawy z zakresu ubezpieczenia społecznego',
            'sprawy karne',
            'sprawy gospodarcze',
            'sprawy w zakresie prawa pracy',
            'sprawy w zakresie prawa rodzinnego',
            'sprawy o wykroczenia',
            'sprawy w zakresie prawa konkurencji'
        ]
        self.tuned_parameters = [{'kernel': ['rbf', 'poly', 'sigmoid'],    'gamma': [1e-1, 1e-2, 1e-3, 1e-4, 1e-5],
                     'C': [1, 10, 100, 1000, 2000, 5000, 10000, 15000]},
                    {'kernel': ['linear'], 'C': [1, 10, 100, 1000, 2000, 5000, 10000, 15000,]}]
        self.scores = ['precision']

    def transform_and_train_classifier(self):
        X_train, Y_train, X_test, Y_test = self.split_into_train_valid_tests(self.__X__, self.__Y__)
        Y_train, Y_test = self.__transform_all_Y_sets__(Y_train, Y_test)
        X_train, X_test = self.__transform_all_X_sets__(X_train, X_test)
        hyper_params = self.__find_best_hyperparamters__(X_train , Y_train)
        clf = self.__train_classifier__(X_train, Y_train, hyper_params)
        result_dict = self.__predict_on_test_set__(clf, X_test, Y_test)
        return result_dict, clf, hyper_params   

    def split_into_train_valid_tests(self, X, Y):
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.25, random_state=42)
        return X_train, Y_train, X_test, Y_test

    def __transform_Y_set__(self, Y):
        Y = np.array([self.category_list.index(category) for category in Y])
        return Y.reshape(-1, 1)

    def __transform_all_Y_sets__(self, Y_train, Y_test):
        return self.__transform_Y_set__(Y_train), self.__transform_Y_set__(Y_test)

    def __transform_all_X_sets__(self, X_train, X_test):
        vectorizer = TfidfVectorizer()
        X_train = vectorizer.fit_transform(X_train)
        X_test = vectorizer.transform(X_test)
        return X_train, X_test

    def __find_best_hyperparamters__(self, X_train, Y_train):
        clf = GridSearchCV(svm.SVC(), self.tuned_parameters, n_jobs=-1)
        clf.fit(X_train, Y_train.flatten())
        return clf.best_params_

    def __train_classifier__(self, X_train, Y_train, best_params):
        C, gamma, kernel = best_params['C'], best_params['gamma'], best_params['kernel']
        clf = svm.SVC(C=C, gamma=gamma, kernel=kernel)
        clf.fit(X_train, Y_train)
        return clf

    def __predict_on_test_set__(self, clf, X_test, Y_test):
        y_predicted = clf.predict(X_test)
        return {
            "accuracy_score": accuracy_score(Y_test, y_predicted),
            "classification_report" : classification_report(Y_test, y_predicted, target_names=self.category_list),
            "micro_report": precision_recall_fscore_support(Y_test, y_predicted, average='micro'),
            "macro_report": precision_recall_fscore_support(Y_test, y_predicted, average='macro')}