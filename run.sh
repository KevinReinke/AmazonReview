#!/usr/bin/bash

hdfs dfs -rm -r -f reviews/reviewerReviewsSample
hdfs dfs -rm -r -f reviews/kmeans_model
if [ $# -eq 0 ] 
	then
	/cluster/spark/bin/spark-submit ReviewerReviews.py
	else
	/cluster/spark/bin/spark-submit ReviewerReviews.py -s $1
fi

cat results.txt
