from pyspark import SparkConf, SparkContext
import json

#run on cluster
confCluster = SparkConf()
confCluster.setMaster("yarn-client")
confCluster.set("spark.driver.host","frontend")
confCluster.setAppName("AmazonReviews")

sc = SparkContext(conf = confCluster)

# Read the data in json format line by line
reviewerReviews = sc.textFile("reviews/reviewerReviews")

# Calculate the counts of reviews for each reviewer
#reviewCounts = reviewerReviews.map(lambda v: len(v[1]))

#numberCounts = sorted(reviewCounts.countByValue().items())



results = reviewerReviews.count()

# Write results to local disk
with open("results2.txt", "w") as f:
	f.write(str(results))

