# Summary: Query-by-committee function for either random forest or Rashomon's TreeFarms that 
#          recommends an observation from the candidate set to be queried.
# Input:
#   Model: The predictive model.
#   df_Candidate: The candidate set.
#   df_Train: The training set.
#   UniqueErrorsInput: A binary input indicating whether to prune duplicate trees in TreeFarms.
# Output:
#   IndexRecommendation: The index of the recommended observation from the candidate set to be queried.

# NOTE: Incorporate covariate GSx in selection criteria? Good for tie breakers.

### Libraries ###
import warnings
import numpy as np
import pandas as pd
from scipy import stats
# from scipy.spatial.distance import cdist
from sklearn.preprocessing import MinMaxScaler

### Function ###
def BatchQBCDiversityFunction(Model, df_Candidate, df_Train, UniqueErrorsInput, DiversityWeight, DensityWeight, BatchSize, auxiliary_columns=None):

    # print("df_Candidate obs: " + str(df_Candidate.shape[0]))

    ### Ignore warning (taken care of) ###
    warnings.filterwarnings("ignore", message="divide by zero encountered in log", category=RuntimeWarning)
    warnings.filterwarnings("ignore", message="invalid value encountered in multiply", category=RuntimeWarning)

    ### Exclude ###
    exclude_cols = ['Y', "DiversityScores", "DensityScores"]

    ### Predicted Values ###
    ## Rashomon Classification ##
    if 'TREEFARMS' in str(type(Model)):

        # Set Up #
        # X_Candidate = df_Candidate[df_Candidate.columns.difference(exclude_cols)]
        X_Candidate = df_Candidate.drop(columns=exclude_cols)
        TreeCounts = Model.get_tree_count()

        # Duplicate #
        PredictionArray_Duplicate = pd.DataFrame(np.array([Model[i].predict(X_Candidate) for i in range(TreeCounts)]))
        PredictionArray_Duplicate.columns = df_Candidate.index.astype(str)
        EnsemblePrediction_Duplicate = pd.Series(stats.mode(PredictionArray_Duplicate)[0])
        EnsemblePrediction_Duplicate.index = df_Candidate["Y"].index
        AllTreeCount = PredictionArray_Duplicate.shape[0]

        # Unique #
        PredictionArray_Unique = pd.DataFrame(PredictionArray_Duplicate).drop_duplicates()
        EnsemblePrediction_Unique = pd.Series(stats.mode(PredictionArray_Unique)[0])
        EnsemblePrediction_Unique.index = df_Candidate["Y"].index
        UniqueTreeCount = PredictionArray_Unique.shape[0]

        if UniqueErrorsInput:
            PredictedValues = PredictionArray_Unique
        else:
            PredictedValues = PredictionArray_Duplicate

        Output = {"AllTreeCount": AllTreeCount,
                  "UniqueTreeCount": UniqueTreeCount}

    ## Random Forest Classification ###
    elif 'RandomForestClassifier' in str(type(Model)):
        # X_Candidate = df_Candidate[df_Candidate.columns.difference(exclude_cols)].values
        X_Candidate = df_Candidate.drop(columns=exclude_cols).values
        PredictedValues = [Model.estimators_[tree].predict(X_Candidate) for tree in range(Model.n_estimators)] 
        PredictedValues = np.vstack(PredictedValues)
        Output = {}

    ### Vote Entropy ###
    VoteC = {}
    LogVoteC = {}
    VoteEntropy = {}
    UniqueClasses = set(df_Train["Y"])

    # Vote entropy per class #
    for classes in UniqueClasses:
        VoteC[classes] = np.mean(PredictedValues == classes, axis=0)
        LogVoteC[classes] = np.log(VoteC[classes])
        VoteEntropy[classes] =  - VoteC[classes] * LogVoteC[classes]
        VoteEntropy[classes] = np.nan_to_num(VoteEntropy[classes], nan=0)
        
    # Vote Entropy #
    VoteEntropyMatrix = np.stack(list(VoteEntropy.values()), axis=1)
    VoteEntropyFinal = np.sum(VoteEntropyMatrix, axis=1)

    # Measures #
    DiversityValues = df_Candidate["DiversityScores"]
    DensityValues = df_Candidate["DensityScores"]

    # Normalize #
    scaler = MinMaxScaler()
    DiversityValues = scaler.fit_transform(np.array(DiversityValues).reshape(-1, 1)).flatten()
    DensityValues = scaler.fit_transform(np.array(DensityValues).reshape(-1, 1)).flatten()
    VoteEntropyFinal = scaler.fit_transform(np.array(VoteEntropyFinal).reshape(-1, 1)).flatten()

    ### Uncertainty Metric ###
    df_Candidate["UncertaintyMetric"] = (1-DiversityWeight - DensityWeight)*VoteEntropyFinal + DiversityWeight*DiversityValues + DensityWeight*DensityValues
    if df_Candidate.shape[0] >= BatchSize:
        IndexRecommendation = list(df_Candidate.sort_values(by = "UncertaintyMetric", ascending = False).index[0:BatchSize])
    else:
        IndexRecommendation = list(df_Candidate.index)
    df_Candidate.drop('UncertaintyMetric', axis=1, inplace=True)

    # Output #
    Output["IndexRecommendation"] = IndexRecommendation

    return Output