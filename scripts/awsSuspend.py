#!/usr/bin/python3
# -*- coding: utf-8 -*-

# --------------------------------------------
# Jaroslaw Glodowski
# version: 1.0
# awsSuspend.py - Refactored awsSuspend 2019/07/04
# Added DBConnect for db communication.
# --------------------------------------------

# Adding a path for the DBConnect in /opt/boru/
import sys
# Required for the DBConnect
sys.path.append("../")
# /opt/boru/DBConnect.py
import DBConnect
# Other imports
import boto3, time, json, logging

def main(jsonDoc):
  # Logger setup
  try:
    logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
    log = logging.getLogger('awsSuspend')
  except Exception as e:
    # Logging* just print, can't log
    print("[awsSuspend] Critical Logger Setup Error: {}".format(str(e)))
    # Exit
    return

  # Extracting the taskId and accountName for the DBConnect to start working from the next step
  try:
    taskId = jsonDoc['task_id']
    accountName = jsonDoc["lab"]
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsSuspend] Critical Error extracting 'taskId' and 'accountName' from 'jsonDoc': {}".format(str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # Extract parameters from main(jsonDoc)
  try:
    region = jsonDoc["region"]
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsSuspend] Critical Error Extracting 'jsonDoc' Parameters: {}".format(str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # variables
  listOfInstancesIdsRaw = []
  listOfInstancesIdsFiltered = []
  listOfInstancesStates = []

  # ==========================
  # Creating the boto3 session
  # ==========================
  try:
    # Session [Most Important] | Used to access student child accounts
    session = boto3.Session(profile_name = accountName, region_name = region)
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsSuspend | {}] Failed to create a boto3 session. Error: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # =============================
  # Getting all EC2 Instances Ids
  # =============================
  try:
    getAllEc2Instances(session, listOfInstancesIdsRaw, listOfInstancesStates, accountName, log)
  except Exception as e:
    errorExceptionInfo = "[awsSuspend | {}] Failed to Get EC2 Instances. Error: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # ================================================
  # Filter any terminated instances to prevent error
  # ================================================
  try:
    if(listOfInstancesIdsRaw):
      filterInstances(listOfInstancesIdsRaw, listOfInstancesStates, listOfInstancesIdsFiltered, accountName, log)
  except Exception as e:
    errorExceptionInfo = "[awsSuspend | {}] Failed to Filter EC2 Instances. Error: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # ==============================
  # Stopping all EC2 Instances Ids
  # ==============================
  if(listOfInstancesIdsFiltered):
    try:
      stopAllEc2Instances(session, listOfInstancesIdsFiltered, accountName, log)
      # give time for the request to go through and start stopping instances
      time.sleep(10)
      # timeout variable
      timeoutCounter = 0

      # check if the instances have stopped
      while True:
        # variables to determine instance status
        instancesStates = []
        completeInstanceStatusCounter = 0
        # getting the state/status of each filtered instance
        for instanceId in listOfInstancesIdsFiltered:
          getInstanceStatus(instanceId, instancesStates, session)
        # if instance is stopped, add +1 to counter for every instance stopped
        for instanceStatus in instancesStates:
          # stack success
          if(instanceStatus == 'stopped'):
            completeInstanceStatusCounter += 1

        # success, the number of stopped instances in the counter matches the length of a list of instances
        if(completeInstanceStatusCounter == len(instancesStates)):
          # update task status to ready
          # DBConnect ============================
          # Update task['taskStatus']
          DBConnect.setTaskStatusToReady(taskId)
          # ======================================
          # logging
          log.info("[awsSuspend | {}] Suspend successfull. Marked task as ready.".format(str(accountName)))
          return

        # exit with timeout of 60 min
        elif(timeoutCounter > 60):
          # update task status error error
          errorExceptionInfo = "[awsSuspend | {}] Timeout error. Marked task as error.".format(str(accountName))
          log.error(errorExceptionInfo)
          # DBConnect ============================
          # Update task['errorInfo']
          DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
          # Update task['taskStatus']
          DBConnect.setTaskStatusToError(taskId)
          # ======================================
          return
        # add to counter
        timeoutCounter += 1
        # sleep timer
        time.sleep(60)
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsSuspend | {}] Failed to Stop EC2 Instances. Error: {}".format(str(accountName), str(e))
      log.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # Update task['taskStatus']
      DBConnect.setTaskStatusToError(taskId)
      # ======================================
      return
  else:
    log.warning("[awsSuspend | {}] No Instances found to stop.".format(str(accountName)))
    # DBConnect ============================
    # Update task['taskStatus']
    DBConnect.setTaskStatusToReady(taskId)
    # ======================================
    return

# Getting all EC2 Instances Ids
def getAllEc2Instances(session, listOfInstancesIdsRaw, listOfInstancesStates, accountName, log):
  # Getting all instances (Not terminated ones)
  ec2Instances = session.client("ec2").describe_instances()
  # logging
  log.info("[awsSuspend | {}] Getting All EC2 Instances...".format(str(accountName)))
  # Add all the instanes Id's into an array
  for instance in ec2Instances["Reservations"]:
    for instance2 in instance["Instances"]:
      listOfInstancesIdsRaw.append(instance2["InstanceId"])
      listOfInstancesStates.append(instance2["State"]["Name"])

# Filter any terminated instances to prevent error
def filterInstances(listOfInstancesIdsRaw, listOfInstancesStates, listOfInstancesIdsFiltered, accountName, log):
  # filtering out any terminated instances from the past that can still be hanging around
  for instanceIndex in range(len(listOfInstancesIdsRaw)):
    if(listOfInstancesStates[instanceIndex] != "terminated"):
      listOfInstancesIdsFiltered.append(listOfInstancesIdsRaw[instanceIndex])
  # logging
  log.info("[awsSuspend | {}] List of Instances to Stop: {}".format(str(accountName), str(listOfInstancesIdsFiltered)))

# Stopping all EC2 Instances Ids
def stopAllEc2Instances(session, listOfInstancesIdsFiltered, accountName, log):
  # stopping all instances
  session.client("ec2").stop_instances(InstanceIds = listOfInstancesIdsFiltered)
  # logging
  log.info("[awsSuspend | {}] Stopping Instances...".format(str(accountName)))

# Getting Status of EC2 Instance
def getInstanceStatus(instanceId, instancesStates, session):
  # getting all information about instance
  ec2InstanceInfo = session.client("ec2").describe_instances(InstanceIds = [instanceId])
  # appending the state of the istance
  for instance in ec2InstanceInfo["Reservations"]:
    for instance2 in instance["Instances"]:
      if(instance2["State"]["Name"] != "terminated"):
        instancesStates.append(instance2["State"]["Name"])

