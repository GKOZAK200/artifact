# Import libraries
import heapq
from collections import defaultdict
from operator import itemgetter

from dataManager import dataManager
from surprise import KNNBasic

# Set current user (user the algorithm is running recommendations for)
currentUser = '173'

# Set k (How many other users are compared to current user)
k = 10

# Set N (How many items will be recommended to the user)
N = 10

# Load data using dataManager
dm = dataManager()
data = dm.loadData()

# Creates training set based on media and ratings data
trainSet = data.build_full_trainset()

# Set parameters for k nearest neighbor (KNN) algorithm
# Cosine similarity method is used (computes the cosine similarity between all pairs of users)
# User based is set to true because this is a user based algorithm instead of an item based one
sim_options = {'name': 'cosine', 'user_based': True}

# Create model
model = KNNBasic(sim_options=sim_options)

# Fit model to training data
model.fit(trainSet)

# Create similarity matrix between users
similarityMatrix = model.compute_similarities()

# Get top N similar users to current user
# (Alternative option to be implemented: select all users up to some similarity threshold)

# Convert user raw ID to inner ID (not sure exactly what that means)
testUserInnerID = trainSet.to_inner_uid(currentUser)

# Creates list of similarity value per user compared to current user (not sure)
similarityRow = similarityMatrix[testUserInnerID]

# Create list of similar users
similarUsers = []
for innerID, score in enumerate(similarityRow):
    if (innerID != testUserInnerID):
        similarUsers.append( (innerID, score) )

# Create list of K most similar users
kNeighbours = heapq.nlargest(k, similarUsers, key=lambda t: t[1])

# Get the media they rated, and add up ratings for each item, weighted by user similarity
candidates = defaultdict(float)
for similarUser in kNeighbours:
    innerID = similarUser[0]
    userSimilarityScore = similarUser[1]
    theirRatings = trainSet.ur[innerID]
    for rating in theirRatings:
        candidates[rating[0]] += (rating[1] / 5.0) * userSimilarityScore

# Build a dictionary of media the user has already seen
watched = {}
for itemID, rating in trainSet.ur[testUserInnerID]:
    watched[itemID] = 1

# Get  top N rated items from similar users:
pos = 0
for itemID, ratingSum in sorted(candidates.items(), key=itemgetter(1), reverse=True):
    if not itemID in watched:
        movieID = trainSet.to_raw_iid(itemID)
        print(dm.getMediaName(int(movieID)), ratingSum)
        pos += 1
        if (pos > N):
            break