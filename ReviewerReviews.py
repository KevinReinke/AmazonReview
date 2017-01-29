from pyspark import SparkConf, SparkContext
import json
import argparse
from os import makedirs
from pyspark.mllib.linalg import Vectors
from pyspark.mllib.feature import PCA
from pyspark.mllib.clustering import KMeans, KMeansModel

# Program parameters
parser = argparse.ArgumentParser()

parser.add_argument("-s", "--sample", type=float, default=0, help="Use a subset of the data. Has to be a number between 0 and 1, determining the size of the subset to use.")

args = parser.parse_args()

subset_size = args.sample

#run on cluster
confCluster = SparkConf()
confCluster.setMaster("yarn-client")
confCluster.set("spark.driver.host","frontend")
confCluster.setAppName("AmazonReviews")

sc = SparkContext(conf = confCluster)

result_collection = {}

# Read the data in json format line by line
file_data = sc.textFile("reviews/reviews_Electronics.json")
# Each dataset is divided by \n --> parse each line into dict
file_data = file_data.map(json.loads)

# Draw a sample from the dataset
if subset_size != 0:
	file_data = file_data.sample(False, subset_size, 79347234)

# Reduce each review to vector of usable data elements
vector_data = file_data.map(lambda d: (d["reviewerID"], (float(d["helpful"][0]) / d["helpful"][1] if d["helpful"][1] != 0 else 0, d["helpful"][1], d["overall"], d["unixReviewTime"], len(d["reviewText"]), len(d["summary"]), len(d["reviewText"].split(" ")), 1)))

# Reduction of reviews per reviewer to vector representing the reviewer
# vectors: (reviewerID, (helpful%, helpful_voted, overall, unixReviewTime, len(reviewText), len(summary), word_count_review_text, reviewCount))
reviewer_vectors = vector_data.reduceByKey(lambda a, b: tuple(a[i] + b[i] for i in range(len(b))))
reviewer_vectors = reviewer_vectors.map(lambda x: (x[0], [val / x[1][7] for val in x[1][:-1]] + [x[1][-1]]))

def averages_per_key(rdd, value_choice_fun):
	trdd = rdd.map(lambda x: (value_choice_fun(x)[0], value_choice_fun(x)[1] + [1]))
	trdd = trdd.reduceByKey(lambda a, b: tuple(a[i] + b[i] for i in range(len(a))))
	trdd = trdd.map(lambda x: (x[0], tuple(val / x[1][-1] for val in x[1][:-1])))
	
	trdd = trdd.sortByKey()

	trdd = trdd.map(lambda x: tuple("{}\t{}\n".format(x[0], x[1][i]) for i in range(len(x[1]))))
	#with open("results.txt", "w") as f:
	#	f.write(str(trdd.first()))
	
	return trdd.reduce(lambda a, b: tuple(a[i] + b[i] for i in range(len(a))))
	

# Get average char count, word count, overall rating and helpful% per review count
review_counts_cc, review_counts_wc, review_counts_or, review_counts_hp = averages_per_key(reviewer_vectors, lambda x: (x[1][7], [x[1][4], x[1][6],  x[1][2], x[1][0]])) 

result_collection["review_counts_char_count"] = review_counts_cc
result_collection["review_counts_word_count"] = review_counts_wc
result_collection["review_counts_overall_rating"] = review_counts_or
result_collection["review_counts_helpful%"] = review_counts_hp


# Get average overall rating per review length (char count)
review_length_cc, = averages_per_key(reviewer_vectors, lambda x: (x[1][4], [x[1][2]]))
review_length_wc, = averages_per_key(reviewer_vectors, lambda x: (x[1][6], [x[1][2]]))

result_collection["review_length_char_count"] = review_length_cc
result_collection["review_length_word_count"] = review_length_wc

# Conduct PCA
reviewer_vectors_real = reviewer_vectors.map(lambda x: Vectors.dense([val for val in x[1]]))

pca_model = PCA(4).fit(reviewer_vectors_real)
transformed = pca_model.transform(reviewer_vectors_real)

current_best = None
current_best_cost = float("inf")

# Run K-Means
for k in range(2, 50, 7):
	kmeans_model = KMeans.train(transformed, k, maxIterations = 100, runs = 10)

	cost = kmeans_model.computeCost(transformed)

	if cost < current_best_cost:
		current_best_cost = cost
		current_best = kmeans_model

#current_best.save(sc, "reviews/kmeans_model")

predicted = current_best.predict(transformed)

predicted_clusters = predicted.zip(reviewer_vectors.map(lambda x: tuple([x[0]] + [val for val in x[1]])))

predicted_clusters = predicted_clusters.sortByKey()

cluster_output = predicted_clusters.map(lambda x: str(x[0]) + "".join("".join(" {}".format(val)) for val in x[1]) + "\n").reduce(lambda a, b: a + b)

result_collection["cluster_output"] = cluster_output

# Write results to local disk
try:
	makedirs("results")
except OSError:
	pass

for key in result_collection:
	with open("results/" + key, "w") as f:
		f.write(str(result_collection[key]))

