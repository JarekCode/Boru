import pandas as pd
import pymongo
# MongoDB connection
mongoClient = pymongo.MongoClient()
mongodb = mongoClient.controllerDB
# Get cursor object
cursor = mongodb.controllers.find()
# Create a dataFrame
df = pd.DataFrame(list(cursor))
# Remove the '_id' from the dataFrame
if('_id' in df):
  del df['_id']
# sort the dataframe as: ['startDate', 'finishDate', 'link']
df = df[['startDate', 'finishDate', 'link']]
# Convert the dataFrame to a .csv file
df.to_csv("/var/log/controllers.csv", index=False)
# clsoe MongoDB
mongoClient.close()