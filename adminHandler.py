#!/usr/bin/python3
# -*- coding: utf-8 -*-

# --------------------------------------------
# Jaroslaw Glodowski
# version: 1.0
# AdminHandler.py - 2019/07/19
# Calls the appropriate createAdmin script in /opt/boru/AdminHandler
# --------------------------------------------

from importlib import import_module
# import all createAdmin scripts for different environments
import sys, pymongo
# This is needed to import the boru python config file
sys.path.insert(0, '/etc/boru/')
import config

# adminScripts
sys.path.append("/opt/boru/adminScripts")
import awsCreateAdmin, awsRemoveAdmin

# ------------
# Create Admin
# ------------
def createAdmin(labName, environment):
  # ----------------
  # mongo connection
  # ----------------
  # setting up the mongo client
  mongoClient = pymongo.MongoClient()
  # specifying the mongo database = 'boruDB'
  mongodb = mongoClient.boruDB

  # 1st Validate the labName and environment. This must be done here because the RequestHandler is not used when creating admins.
  response = validateLabIsInLabsColletion(labName, environment, mongodb)
  if(not response):
    # closing mongo connection
    mongoClient.close()
    # Return error to user
    error = "[AdminHandler] Failed to schedule class: The Lab: 'labName':'{}', 'environment':'{}' provided by user is not valid.".format(str(labName), str(environment))
    return {"error": error}

  # Add additional information to be passed into a createAdmin script.
  adminUserName = config.getConfig("AdminUserName")
  groupName = config.getConfig("AdminGroupName")
  password = config.getConfig("AdminPassword")
  region = config.getConfig("AdminRegionForBoto3")
  adminPolicyJson = config.getConfig("AdminPolicyJson")
  adminPolicyName = config.getConfig("AdminPolicyName")

  # All of the above in 1 dict
  # Information required to be passed into any createAdmin script:
  infoToPassIntoCreateAdminScript = { \
      "labName" : labName,\
      "userName" : adminUserName,\
      "groupName" : groupName,\
      "password" : password,\
      "region" : region,\
      "adminPolicyJson" : adminPolicyJson,\
      "adminPolicyName" : adminPolicyName }

  # Name of the script info will be passed into
  createAdminScriptNameRaw = config.getConfig("createAdminScriptNamesForEnvironment")
  # will be there because it was checked in validateLabIsInLabsColletion() above
  for i in createAdminScriptNameRaw:
    if(i.get(str(environment))):
      nameOfcreateAdminScript = i.get(str(environment))
  # Convert the string above to a runnable module
  scriptName = import_module(str(nameOfcreateAdminScript))
  # Call the script and get the resopnse
  print("Calling '{}' script with: {}".format(str(labName), str(infoToPassIntoCreateAdminScript)))
  response = scriptName.createAdmin(infoToPassIntoCreateAdminScript)
  # Return the response from createAdminScript
  return response


# ------------
# Remove Admin
# ------------
def removeAdmin(labName, environment):
  # ----------------
  # mongo connection
  # ----------------
  # setting up the mongo client
  mongoClient = pymongo.MongoClient()
  # specifying the mongo database = 'boruDB'
  mongodb = mongoClient.boruDB

  # 1st Validate the labName and environment. This must be done here because the RequestHandler is not used when creating admins.
  response = validateLabIsInLabsColletion(labName, environment, mongodb)
  if(not response):
    # closing mongo connection
    mongoClient.close()
    # Return error to user
    error = "[AdminHandler] Failed to schedule class: The Lab: 'labName':'{}', 'environment':'{}' provided by user is not valid.".format(str(labName), str(environment))
    return {"error": error}

  # Add additional information to be passed into a removeAdmin script.
  adminUserName = config.getConfig("AdminUserName")
  groupName = config.getConfig("AdminGroupName")
  region = config.getConfig("AdminRegionForBoto3")
  adminPolicyName = config.getConfig("AdminPolicyName")

  # All of the above in 1 dict
  # Information required to be passed into any removeAdmin script:
  infoToPassIntoRemoveAdminScript = { \
      "labName" : labName,\
      "userName" : adminUserName,\
      "groupName" : groupName,\
      "region" : region,\
      "adminPolicyName" : adminPolicyName }

  # Name of the script info will be passed into
  removeAdminScriptNameRaw = config.getConfig("removeAdminScriptNamesForEnvironment")
  # will be there because it was checked in validateLabIsInLabsColletion() above
  for i in removeAdminScriptNameRaw:
    if(i.get(str(environment))):
      nameOfremoveAdminScript = i.get(str(environment))
  # Convert the string above to a runnable module
  scriptName = import_module(str(nameOfremoveAdminScript))
  # Call the script and get the resopnse
  print("Calling '{}' script with: {}".format(str(labName), str(infoToPassIntoRemoveAdminScript)))
  response = scriptName.removeAdmin(infoToPassIntoRemoveAdminScript)
  # Return the response from removeAdminScript
  return response


# Validate Lab Is In Labs Colletion
def validateLabIsInLabsColletion(labName, environment, mongodb):
  allLabNames = []
  allLabEnvironments = []
  # Get a list of all Labs in the labs collection and return error if the user specified lab does not exits there.
  fullLabsInfo = mongodb.labs.find()
  for i in fullLabsInfo:
    allLabNames.append(i['labName'])
    allLabEnvironments.append(i['environment'])
  # Check the 'labName' and 'environment'
  if(str(labName) in allLabNames):
    index = allLabNames.index(str(labName))
    if(str(allLabEnvironments[index]) == str(environment)):
      return True
    else:
      return False
  else:
    return False