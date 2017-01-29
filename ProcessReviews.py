from pyspark import SparkConf, SparkContext
import json

#run on cluster
#confCluster = SparkConf()
#confCluster.setMaster("yarn-client")
#confCluster.set("spark.driver.host","frontend")
#confCluster.setAppName("AmazonReviews")

#sc = SparkContext(conf = confCluster)


review_vectors = testvals

# Reduction of reviews per reviewer to vector representing the reviewer
#reviewer_vectors = review_vectors.reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1], a[2] + b[2]))#, a[3] + b[3], a[4] + b[4], a[5] + b[5], a[6] + b[6]))

results = reviewer_vectors.first()

# Write results to local disk
#with open("results2.txt", "w") as f:
#	f.write(str(results))

