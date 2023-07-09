import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_squared_error, r2_score, explained_variance_score, mean_absolute_error
from pytorch_tabnet.tab_model import TabNetRegressor
import seaborn as sns
from matplotlib import pyplot


# Reading the data
file_path = "C:/Users/Ariel/Documents/CV/Assigment/SurgeriesToPredict.csv"  
df = pd.read_csv(file_path)

# Setting the types currectly
df["DoctorID"] = df["DoctorID"].astype(str)
df["AnaesthetistID"]= df["AnaesthetistID"].astype(str)
df['Anesthesia Type'] = df['Anesthesia Type'].astype('bool')

# Removing the first unnecessary column (running numbering)
RelevantData = df.iloc[:, 1:];

# *** Data cleaning ****
# Removing duplicted rows
deduplicated_data = RelevantData.drop_duplicates(subset=['Surgery Type','Anesthesia Type','Age', 'BMI','DoctorID', 'AnaesthetistID'])

# Spliting the table to features(X) and target (y)
X = deduplicated_data.iloc[:, :-1]
y = deduplicated_data.iloc[:, -1]

# Splitting the data to train set and test set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Presneting the input data distribution and connections
train_dataset = X_train.copy()
train_dataset.insert(0, "Duration", y_train)
_ = sns.pairplot(
    train_dataset[
        ["Duration", "Surgery Type", "Anesthesia Type", "Age", "BMI"]
    ], kind="reg", diag_kind="kde",plot_kws={"scatter_kws": {"alpha": 0.1}},)
    
# Defining and running extra tree regressor
reg = ExtraTreesRegressor(n_estimators=500, max_depth = 9, random_state = 18).fit( X_train, y_train)
predictions_extra = reg.predict(X_test) 

# printing some metrics 
print(f"model score on training data: {reg.score(X_train, y_train)}")
print(f"model score on testing data: {reg.score(X_test, y_test)}")
print(f"model MSE on training data: {mean_squared_error(y_test, predictions_extra)}")
print(f"model MAE on training data: {mean_absolute_error(y_test, predictions_extra)}")

# Defining and running TabNet regressor
clf = TabNetRegressor()
clf.fit(X_train, y_train, eval_set=[(X_test, y_test)])
preds = clf.predict(X_test)

# printing some metrics 
print(f"model score on training data: {clf.score(X_train, y_train)}")
print(f"model score on testing data: {clf.score(X_test, y_test)}")
print(f"model MSE on training data: {mean_squared_error(y_test, preds)}")
print(f"model MAE on training data: {mean_absolute_error(y_test, preds)}")

# Printing ans showing the features importance
feature_names = list(X.columns) #deduplicated_data[:-1].keys()
importance = reg.feature_importances_
for i,v in enumerate(feature_names):
    print('%s: %.5f' % (v, importance[i]))
pyplot.barh(feature_names, importance)
pyplot.show()

# Permutation importance
def get_score_after_permutation(model, X, y, curr_feat):
    X_permuted = X.copy()
    col_idx = list(X.columns).index(curr_feat)
    # permute one column
    X_permuted.iloc[:, col_idx] = np.random.permutation(X_permuted[curr_feat].values)
    permuted_score = model.score(X_permuted, y)
    return permuted_score

def get_feature_importance(model, X, y, curr_feat):
    baseline_score_train = model.score(X, y)
    permuted_score_train = get_score_after_permutation(model, X, y, curr_feat)

    # feature importance is the difference between the two scores
    feature_importance = baseline_score_train - permuted_score_train
    return feature_importance

# Permutation importance for all features - with statistics on 10 repeats
def permutation_importance(model, X, y, n_repeats=10):
    importances = []
    for curr_feat in X.columns:
        list_feature_importance = []
        for n_round in range(n_repeats):
            list_feature_importance.append(get_feature_importance(model, X, y, curr_feat))
        importances.append(list_feature_importance)

    return {
        "importances_mean": np.mean(importances, axis=1),
        "importances_std": np.std(importances, axis=1),
        "importances": importances,
    }

# plot the feature importances
def plot_feature_importances(perm_importance_result, feat_name):
    fig, ax = pyplot.subplots()

    indices = perm_importance_result["importances_mean"].argsort()
    pyplot.barh(
        range(len(indices)),
        perm_importance_result["importances_mean"][indices],
        xerr=perm_importance_result["importances_std"][indices],
    )

    ax.set_yticks(range(len(indices)))
    _ = ax.set_yticklabels(feat_name[indices])

# plot permutation importance
perm_importance_result_train = permutation_importance(reg, X_train, y_train, n_repeats=10)
plot_feature_importances(perm_importance_result_train, X_train.columns)