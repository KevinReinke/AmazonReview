from pyspark import SparkConf, SparkContext
import json

#run on cluster
confCluster = SparkConf()
confCluster.setMaster("yarn-client")
confCluster.set("spark.driver.host","frontend")
confCluster.setAppName("AmazonReviews")

#run on local machine
#confLocal = SparkConf().setMaster("local").setAppName("Spark Test Local")	

sc = SparkContext(conf = confCluster)

# Read the data in json format line by line
filedata = sc.textFile("reviews/reviews_Electronics.json")
# Each dataset is divided by \n --> parse each line into dict
filedata = filedata.map(json.loads)

with open("filedata.txt", "w") as f:
	f.write(str(filedata.take(10)))

# The reviews for each reviewer
reviewerReviews = filedata.groupBy(lambda v: v["reviewerID"]).map(lambda x: (x[0], list(x[1])))

results = reviewerReviews.take(1)

# Write results to local disk
with open("results.txt", "w") as f:
	f.write(str(results))

