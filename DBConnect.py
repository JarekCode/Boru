#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Jaroslaw Glodowski
# DBConnect.py

# Last updated: 05/Jul/2019
# Last Update: Added 'raise Exception' to all functions

import pymongo, logging
from bson import ObjectId

# Logger setup
logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
log = logging.getLogger('DBConnect')

# MongoDB setup
mongoClient = pymongo.MongoClient()
mongodb = mongoClient.boruDB

# Sets task['taskStatus'] to error
def setTaskStatusToError(taskId):
  try:
    mongodb.tasks.update_one({ "_id": ObjectId(taskId) }, { "$set": { "taskStatus": "error" } })
    log.info("[DBConnect] Task '{}': Status set to 'error'".format(str(taskId)))
  except Exception as e:
    errorExceptionInfo = "[DBConnect] 'setTaskStatusToError' Failed: {}".format(str(e))
    log.exception(errorExceptionInfo)
    raise Exception(errorExceptionInfo)

# Sets task['taskStatus'] to ready
def setTaskStatusToReady(taskId):
  try:
    mongodb.tasks.update_one({ "_id": ObjectId(taskId) }, { "$set": { "taskStatus": "ready" } })
    log.info("[DBConnect] Task '{}': Status set to 'ready'".format(str(taskId)))
  except Exception as e:
    errorExceptionInfo = "[DBConnect] Function 'setTaskStatusToReady' Failed: {}".format(str(e))
    log.exception(errorExceptionInfo)
    raise Exception(errorExceptionInfo)

# Add error information to task['errorInfo']
def appendTaskErrorInfo(taskId, accountName, error):
  try:
    mongodb.tasks.update_one({ "_id": ObjectId(taskId) }, { "$push": { "errorInfo": str(accountName) } })
    mongodb.tasks.update_one({ "_id": ObjectId(taskId) }, { "$push": { "errorInfo": str(error) } })
    log.info("[DBConnect] Task '{}': Appended error information: '{}' for account: {}".format(str(taskId), str(error), str(accountName)))
  except Exception as e:
    errorExceptionInfo = "[DBConnect] Function 'appendTaskErrorInfo' Failed: {}".format(str(e))
    log.exception(errorExceptionInfo)
    raise Exception(errorExceptionInfo)

# Add information to task['successInfo']
def appendTaskSuccessInfo(taskId, accountName, item):
  try:
    mongodb.tasks.update_one({ "_id": ObjectId(taskId) }, { "$push": { "successInfo": accountName } })
    mongodb.tasks.update_one({ "_id": ObjectId(taskId) }, { "$push": { "successInfo": item } })
    log.info("[DBConnect] Task '{}': Appended success information: '{}' for account: {}".format(str(taskId), str(item), str(accountName)))
  except Exception as e:
    errorExceptionInfo = "[DBConnect] Function 'appendTaskSuccessInfo' Failed: {}".format(str(e))
    log.exception(errorExceptionInfo)
    raise Exception(errorExceptionInfo)

# Returns course['sensorParameters']
def returnCourseSensorParameters(courseName):
  try:
    courseSensorParameters = mongodb.courses.find_one({"courseName" : str(courseName)}, {"sensorParameters":1, "_id":0})
    log.info("[DBConnect] Returned course['sensorParameters'] for the {} course.".format(str(courseName)))
    return courseSensorParameters
  except Exception as e:
    errorExceptionInfo = "[DBConnect] Function 'returnCourseSensorParameters' Failed: {}".format(str(e))
    log.exception(errorExceptionInfo)
    raise Exception(errorExceptionInfo)

