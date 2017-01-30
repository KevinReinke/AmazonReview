from pyspark import SparkConf, SparkContext
import json
import argparse
from os import makedirs

#run on cluster
confCluster = SparkConf()
confCluster.setMaster("yarn-client")
confCluster.set("spark.driver.host","frontend")
confCluster.setAppName("AmazonReviews")

sc = SparkContext(conf = confCluster)

result_collection = {}

input_filename = "cluster_output64"

# Read the data in json format line by line
file_data = sc.textFile("reviews/" + input_filename)

file_data = file_data.map(lambda x: x.split(" "))
file_data = file_data.map(lambda x: (int(x[0]), (x[1], float(x[2]), int(x[3]), float(x[4]), int(x[5]), float(x[6]), float(x[7]), float(x[8]), float(x[9]))))

# Reduce each review to vector of usable data elements
#vector_data = file_data.map(lambda d: (d["reviewerID"], (float(d["helpful"][0]) / d["helpful"][1] if d["helpful"][1] != 0 else 0, d["helpful"][1], d["overall"], d["unixReviewTime"], len(d["reviewText"]), len(d["summary"]), len(d["reviewText"].split(" ")), 1)))

# Reduction of reviews per reviewer to vector representing the reviewer
# vectors: (reviewerID, (helpful%, helpful_voted, overall, unixReviewTime, len(reviewText), len(summary), word_count_review_text, reviewCount))

def averages_all_keys(rdd, value_choice_fun):
	trdd = rdd.map(lambda x: (value_choice_fun(x)[0], value_choice_fun(x)[1] + [1]))
	trdd = trdd.reduceByKey(lambda a, b: tuple(a[i] + b[i] for i in range(len(a))))
	trdd = trdd.map(lambda x: (x[0], tuple(val / x[1][-1] for val in x[1][:-1])))
	
	trdd = trdd.sortByKey()

	trdd = trdd.map(lambda x: str(x[0]) + " "  + "".join(" ".join("{}".format(val) for val in x[1])) + "\n")
	#with open("results.txt", "w") as f:
	#	f.write(str(trdd.first()))
	
	return trdd.reduce(lambda a, b: a + b)
	

# Get average char count, word count, overall rating and helpful% per review count
averages = averages_all_keys(file_data, lambda x: (x[0], [x[1][1], x[1][2], x[1][3], x[1][4], x[1][5], x[1][6], x[1][7], x[1][8]])) 

result_collection[input_filename] = averages

# Write results to local disk
try:
	makedirs("results/cluster_results")
except OSError:
	pass

for key in result_collection:
	with open("results/cluster_results/" + key, "w") as f:
		f.write(str(result_collection[key]))

