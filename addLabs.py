# -*- coding: utf-8 -*-
# Jaroslaw Glodowski
# script: addLabs.py
# version: 1.0.2

import pymongo, json
# This is needed to import the boru python config file
import sys
sys.path.insert(0, '/etc/boru/')
import config

def addLabs(labName, rangeFrom, rangeTo, environment):


  # Setting up mongoDB client
  mongoClient = pymongo.MongoClient()
  mongodb = mongoClient.boruDB

  # Very first thing, validate all the parameters to prevent crashes
  response = validateParameters(labName, rangeFrom, rangeTo, environment)
  if(response[0]):
    return {"error": response[1]}

  # ------------------------------------------
  # Validate Labs not all ready in database
  # ------------------------------------------
  counter = int(rangeFrom)
  for i in range(counter, int(rangeTo) + 1):
    # Check against the database
    if(counter < 10 ):
      response = checkIfLabExists(str(labName) + '0' + str(i), mongodb)
    else:
      response = checkIfLabExists(str(labName) + str(i), mongodb)
    # Check response
    if(response[0]):
      error = "Lab '{}' exists in the database".format(response[1])
      return {"error": error}
  # -------------------
  # Update the database
  # -------------------
  # Add a range of labs to the database as all labs are not duplicates
  counter = int(rangeFrom)
  for i in range(counter, int(rangeTo) + 1):
    if(counter < 10 ):
      mongodb.labs.insert({'labName' : str(labName) + '0' + str(i), 'status' : 'free', 'jobID' : ' ', 'environment' :  str(environment)})
      # Add the lab to config file
      # call_script_here
    else:
      mongodb.labs.insert({'labName' : str(labName) + str(i), 'status' : 'free', 'jobID' : ' ', 'environment' :  str(environment)})
      # Add the lab to config file
      # call_script_here
  # Closing Mongo Connection 
  mongoClient.close()
  success = "The database has been updated"
  return {"success": success}

# Validates the user input and returns True if fails
def validateParameters(labName, rangeFrom, rangeTo, environment):
  # 1: labName - Requirements: type: str
  if(isinstance(labName, str) == False):
    return [True, "'labName' must be of type 'str'"]
  # 2: rangeFrom - Requirements: type: int, must be > 0
  try:
    if(int(rangeFrom) <= 0):
      return [True, "'rangeFrom' must be bigger than '0'"]
  except:
    return [True, "'rangeFrom' must be of type 'int'"]
  # 3: rangeTo - Requirements: type: int, must be > 0
  try:
    if(int(rangeTo) <= 0):
      return [True, "'rangeTo' must be bigger than '0'"]
  except:
    return [True, "'rangeTo' must be of type 'int'"]
  # 4: Must be: rangeFrom <= rangeTo
  if(int(rangeFrom) > int(rangeTo)):
    return [True, "'rangeFrom' must be less or equal [<=] to 'rangeTo'"]
  # 5: environment - Requirements: type: str, must be in db.config['region'] Eg: 'aws'
  if(isinstance(environment, str) == False):
    return [True, "'environment' must be of type 'str'"]
  # Check against db.config['region']
  listOfEnvrionments = []
  errorStr = ""

  try:
    configRegion = config.getConfig("region")
  except Exception as e:
    errorMessage = "[addLabs] Error: {} in config.py. Please update config.py and run 'restartBoru'".format(str(e))
    return [True, errorMessage]

  for i in configRegion:
      listOfEnvrionments.append(list(i.keys()))
  # check against the 'listOfEnvrionments'
  for i in listOfEnvrionments:
    errorStr = errorStr + i[0] + ", "
    if(environment == i[0]):
      return [False, "N/A"]
  return [True, "'environment' must be one of the following: [ {}]".format(str(errorStr))]

# Checks if a lab is in the database
def checkIfLabExists(labName, mongodb):
  print("SbOrg:", labName)
  # Get all labs
  allLabs = mongodb.labs.find()
  # Look for the lab and return True if it is found
  for lab in allLabs:
    if(str(lab['labName']).lower() == str(labName).lower()):
      return [True, labName]
  return [False, labName]
