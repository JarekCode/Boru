#!/usr/bin/python3
# -*- coding: utf-8 -*-

# --------------------------------------------
# Jaroslaw Glodowski
# version: 1.2
# awsStart.py - Added appendInternalAndExternalIpsForSuccessInfo() 2019/08/20
# Added DBConnect for db communication.
# --------------------------------------------

# Adding a path for the DBConnect in /opt/boru/
import sys
# Required for the DBConnect
sys.path.append("../")
# Required for processing sensor parameters and the creation of the sensor (Must be done in awsStart)
sys.path.append("../boru/plugins")

# Other imports
import boto3, json, time, logging, datetime
from importlib import import_module
# /opt/plugins/*
from plugins import *
# /opt/boru/DBConnect.py
import DBConnect

def main(jsonDoc):
  # Example of 'jsonDoc'
  '''
  {
    "task_id" : "abc111555566abbca",
    "lab" : "Student01",
    "courseName" : "ANYDC",
    Everything passed in from the 'generateStartLabTaskBuffer' function in the scheduler,
    along with cloudFormation parameters processed by the scheduler.
  }
  '''

  # Logger setup
  try:
    logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
    log = logging.getLogger('awsStart')
  except Exception as e:
    # Logging* just print, can't log
    print("[awsStart] Critical Logger Setup Error: {}".format(str(e)))
    # Exit
    return

  # Extracting the taskId and accountName for the DBConnect to start working from the next step
  try:
    taskId = jsonDoc['task_id']
    accountName = jsonDoc['lab']
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsStart] Critical Error extracting 'taskId' and 'accountName' from 'jsonDoc': {}".format(str(e))
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
    courseName = jsonDoc['courseName']
    startDate = jsonDoc['startDate']
    finishDate = jsonDoc['finishDate']
    timezone = jsonDoc['timezone']
    instructor = jsonDoc['instructor']
    tag = jsonDoc['tag']
    region = jsonDoc['region']
    cloudFormationParameters = jsonDoc['parameters']
    startTemplateUrl = jsonDoc['courseTemplate']
    sensorTemplate = jsonDoc['sensorTemplate']
    sensor = jsonDoc['sensor']
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsStart] Critical Error Extracting 'jsonDoc' Parameters: {}".format(str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  ''' Below the main stuff happens '''
  # Just a sleep timer variable. Call him Gary
  garyTheSnail = 30

  # ===================
  # Generate Stack Name
  # ===================
  # The stackName will look similar to: 'ANYDC-2-4Jul-Central-joriordan-ANYDC-CET-LabsTest'
  # This name will be passed into 'cloudFormation.create_stack' as the 'StackName'
  ''' !!! If ANYDC removed from tag, add courseName to start, Else, dont add courseName'''
  try:
    stackName = generateStackName(courseName, startDate, finishDate, timezone, instructor, tag)
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsStart | {}] Error generating the stack name: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # ====================================================
  # Create a boto3 session and a cloudFormation resource
  # ====================================================
  # Creating the boto3 session that will communicate with AWS.
  # Creating a session resource for a cloudFormation
  try:
    session = boto3.Session(profile_name = accountName, region_name = region)
    cloudFormation = session.resource('cloudformation')
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsStart | {}] Error creating the boto3 session: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # ==================================================================
  # Extracting all cloudFormationParameters from jsonDoc['parameters']
  # ==================================================================
  # Extracting all the raw parameters into lists that will be used to create a
  # 'cloudFormationParametersBuffer', which will be passed into 'cloudFormation.create_stack'
  try:
    # Buffer, will be ignored
    parametersKeysBuffer = []
    parametersValsBuffer = []
    # Add to the buffer
    for param in cloudFormationParameters[0]:
      parametersKeysBuffer.append(list(param.keys()))
      parametersValsBuffer.append(list(param.values()))

    # Final keys and values
    cloudFormationParametersKeys = []
    cloudFormationParametersVals = []

    # Extracting keys
    for item in parametersKeysBuffer:
      cloudFormationParametersKeys.append(item[0])
    # Extracting values
    for item in parametersValsBuffer:
      cloudFormationParametersVals.append(item[0])
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsStart | {}] Error extracting cloudFormation parameters: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # ================================
  # cloudFormation Parameters Buffer
  # ================================
  # This buffer is passed into 'cloudFormation.create_stack'
  try:
    # The buffer containing all cloudFormationParametersKeys and parametersValsBuffer ready for 'cloudFormation.create_stack'
    parametersBuffer = []
    # Creating the buffer
    for paramIndex in range(len(cloudFormationParametersKeys)):
      parametersBuffer.append({'ParameterKey': str(cloudFormationParametersKeys[paramIndex]), 'ParameterValue': str(cloudFormationParametersVals[paramIndex])})
    # logging
    log.info("[awsStart | {}] Course Parameters Buffer: {}".format(str(accountName), str(parametersBuffer)))
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsStart | {}] Error creating cloudFormation parameters buffer: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # =====================
  # Cloud Formation Stack
  # =====================
  # Creating the cloudFormation stack in AWS using 'cloudFormation.create_stack'
  try:
    cloudFormation.create_stack(StackName = str(stackName), TemplateURL = str(startTemplateUrl), Parameters = parametersBuffer, Capabilities=['CAPABILITY_NAMED_IAM'])
    # logging
    log.info("[awsStart | {}] starting course cloudFormation...".format(str(accountName)))
    # Wait Gary number seconds to give time for AWS to set up stacks. Stack creation will take many minutes anyway
    time.sleep(garyTheSnail)
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsStart | {}] Error creating AWS stack: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return

  # =====================
  # |Query the AWS Stack|
  # =====================
  # Query the AWS Stack and wait until it finishes deploying or until a timeout is reached.
  response = queryAllStacks(session, accountName, log)
  # If stacks failed to deploy, update task to error, log and exit
  if(response):
    # Logging
    errorExceptionInfo = "[awsStart | {}] Error AWS stack(s) failed to deploy.".format(str(accountName))
    log.error(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # Exit
    return
  # Need to get the stack info now BUT not store it yet as the senson might need to be spun up.
  # If queryStackAndReturnInfo() is called after the sensor is up, it will return the sensor output, so do it now and store it.
  successInfoToAppendToTask = queryStackAndReturnInfo(session, taskId, accountName, log)

  # ======
  # Sensor
  # ======

  # Check if a sensor is required
  if(sensor == "yes"):
    # =====================
    # Get Sensor Parameters
    # =====================
    # Get the course['sensorParameters'] from the DBConnect
    courseSensorParameters = DBConnect.returnCourseSensorParameters(courseName)

    # Create lists used for each parameted. All of them are sorted by index.
    listOfSensorParamFiles = []
    listOfSensorParamKeys = []
    listOfSensorParamValues = []
    listOfSensorParamTypes = []
    # Processed final values used for the buffer.
    listOfSensorParamValuesProcessed = []

    # =========================
    # Process Sensor Parameters
    # =========================
    # Append all the information about each sensor parameter to lists.
    # All lists are ordered by index
    for param in courseSensorParameters['sensorParameters']:
      listOfSensorParamFiles.append(param['paramFile'])
      listOfSensorParamKeys.append(param['paramKey'])
      listOfSensorParamValues.append(param['paramValue'])
      listOfSensorParamTypes.append(param['paramType'])

    # Now the big part, processing the sensor parameters. This must be done in the awsStart script and not the scheduler.
    # This is done because some parameters require the course cloudFormation to be up and running. (It creates things required for the sensor)
    try:
      # Go through each parameter and process it. The final processed result is appended to 'listOfSensorParamValuesProcessed' (Plugins need to be processed)
      for index in range(len(listOfSensorParamFiles)):
        # There are two types of sensor parameters possible, 'plugin-static' and 'static'
        # -------------
        # plugin-static
        # -------------
        if(listOfSensorParamTypes[index] == "plugin-static"):
          # Get the paramFile as it is required to process the plugin
          paramFile = listOfSensorParamFiles[index]
          # Get the Key of the parameter
          paramKey = listOfSensorParamKeys[index]
          # Get the static Value of the parameter stored in DB as it is static
          paramUnprocessedValue = listOfSensorParamValues[index]
          # ---
          # Now run and process the parameter as it is a plugin
          sensorParamProcessedValue = sensorParameterPluginStatic(paramFile, paramUnprocessedValue, accountName, region)
          for key in sensorParamProcessedValue:
            value = sensorParamProcessedValue[key]
            if(checkParamValueForError(key)):
              # Logging
              errorExceptionInfo = "[awsStart | {}] Failed to process plugin parameter: {}. Plugin response: {}".format(str(accountName), str(key), str(value))
              log.error(errorExceptionInfo)
              # DBConnect ============================
              # Update task['errorInfo']
              DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
              # Update task['taskStatus']
              DBConnect.setTaskStatusToError(taskId)
              # ======================================
              # Exit
              return
            else:
              listOfSensorParamValuesProcessed.append(str(value))
        # There are two types of sensor parameters possible, 'plugin-static' and 'static'
        # ------
        # static
        # ------
        elif(listOfSensorParamTypes[index] == "static"):
          # Append the static param value. No processing required as it is not a plugin
          listOfSensorParamValuesProcessed.append(str(listOfSensorParamValues[index]))
        # All other types are not supporded for now
        # No other parameter types accapted. Return error
        else:
          # Logging
          error = "[awsStart | {}] Sensor parameter Type '{}' not accepted for sensor Parameters.".format(str(accountName), str(listOfSensorParamTypes[index]))
          log.error(error)
          # DBConnect ============================
          # Update task['errorInfo']
          DBConnect.appendTaskErrorInfo(taskId, accountName, error)
          # Update task['taskStatus']
          DBConnect.setTaskStatusToError(taskId)
          # ======================================
          # Exit
          return
    except Exception as e:
      # Logging
      errorExceptionInfo = "[awsStart | {}] Error processing sensor parameters: {}".format(str(e))
      log.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # Update task['taskStatus']
      DBConnect.setTaskStatusToError(taskId)
      # ======================================
      # Exit
      return
    # ========================
    # Sensor Parameters Buffer
    # ========================
    # This buffer is passed into 'cloudFormation.create_stack'
    try:
      # The buffer containing all sensorParametersKeys and parametersValsBuffer ready for 'cloudFormation.create_stack'
      parametersBuffer = []
      # Creating the buffer
      for paramIndex in range(len(listOfSensorParamKeys)):
        parametersBuffer.append({'ParameterKey': str(listOfSensorParamKeys[paramIndex]), 'ParameterValue': str(listOfSensorParamValuesProcessed[paramIndex])})
      # logging
      log.info("[awsStart | {}] Course Parameters Buffer: {}".format(str(accountName), str(parametersBuffer)))
    except Exception as e:
      # Logging
      errorExceptionInfo = "[awsStart | {}] Error creating sensor parameters buffer: {}".format(str(accountName), str(e))
      log.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # Update task['taskStatus']
      DBConnect.setTaskStatusToError(taskId)
      # ======================================
      # Exit
      return

    # =====================
    # Cloud Formation Stack
    # =====================
    # Creating the cloudFormation stack in AWS using 'cloudFormation.create_stack'
    try:
      cloudFormation.create_stack(StackName = "Sensor", TemplateURL = str(sensorTemplate), Parameters = parametersBuffer, Capabilities=['CAPABILITY_NAMED_IAM'])
      # logging
      log.info("[awsStart | {}] starting sensor cloudFormation...".format(str(accountName)))
      # Wait Gary number seconds to give time for AWS to set up stacks. Stack creation will take many minutes anyway
      time.sleep(garyTheSnail)
    except Exception as e:
      # Logging
      errorExceptionInfo = "[awsStart | {}] Error creating AWS stack: {}".format(str(accountName), str(e))
      log.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # Update task['taskStatus']
      DBConnect.setTaskStatusToError(taskId)
      # ======================================
      # Exit
      return

    # =====================
    # |Query the AWS Stack|
    # =====================
    # Query the AWS Stack and wait until it finishes deploying or until a timeout is reached.
    response = queryAllStacks(session, accountName, log)
    # If stacks failed to deploy, update task to error, log and exit
    if(response):
      # Logging
      errorExceptionInfo = "[awsStart | {}] Error AWS sensor stack(s) failed to deploy.".format(str(accountName))
      log.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # Update task['taskStatus']
      DBConnect.setTaskStatusToError(taskId)
      # ======================================
      # Exit
      return

    # ===============================================================================
    # Adding --protocol all to a security group begining with "Sensor-USM-ServicesSG"
    # ===============================================================================
    response = addProtocolAllToSensorUSMServicesSG(session, accountName, log)
    # If adding the security group fails, update task to error, log and exit
    if(response[0]):
      # Logging
      errorExceptionInfo = "[awsStart | {}] Failed to add --protocol all to Sensor-USM-ServicesSG security group. Error: {}".format(str(accountName), str(response[1]))
      log.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # Update task['taskStatus']
      DBConnect.setTaskStatusToError(taskId)
      # ======================================
      # Exit
      return

    # Add sensor public and private IP's
    successInfoToAppendToTask = appendInternalAndExternalIpsForSuccessInfo(session, successInfoToAppendToTask, accountName, log)

    # Add the output information from the cloudFormation to task['successInfo']
    addStackSuccessInfoToTask(session, taskId, accountName, successInfoToAppendToTask)

    # After the sensor is up, now we can finish the task successfully
    # DBConnect ============================
    # Update task['taskStatus']
    DBConnect.setTaskStatusToReady(taskId)
    # ======================================

  # Jump to here if no sensor is required and mark the task successfully
  else:
    # Add the output information from the cloudFormation to task['successInfo']
    addStackSuccessInfoToTask(session, taskId, accountName, successInfoToAppendToTask)

    # DBConnect ============================
    # Update task['taskStatus']
    DBConnect.setTaskStatusToReady(taskId)
    # ======================================

  # End of awsStart ========================

# This function generates a stackName for AWS.
def generateStackName(courseName, startDate, finishDate, timezone, instructor, tag):
  # get day of startDate for the stackName
  startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d %H:%M:%S")
  startDateDay = startDate.day
  # get day and month of finishDate for the stackName
  finishDate = datetime.datetime.strptime(finishDate, "%Y-%m-%d %H:%M:%S")
  finishDateDay = finishDate.day
  finishDateMonth = finishDate.month
  finishDateMonth = convertMonthIntToSrt(finishDateMonth)
  # get timezone, the word after '/' for the stackName
  timezone = timezone.split("/",1)[1]
  # the final stackName
  stackName = str(courseName) + '-' + str(startDateDay) + '-' + str(finishDateDay) + str(finishDateMonth) + '-' + str(timezone) + '-' + str(instructor) + '-' + str(tag)
  # return stackName
  return stackName

# This function queries AWS every 60 seconds and checks if the stacks have deployed correctly.
# The failFlag boolean is returned False = ALL GOOD, True = SOMETHING BAD
def queryAllStacks(session, accountName, log):
  try:
    # Timeout counter variable
    timeoutCounter = 0
    # Fail flag, set when a task timeouts or has one of the unsuccessful states like: CREATE_FAILED
    failFlag = False
    # Loop until a timeout is reached (will break out of loop)
    while(True):
      # Get all stacks in the account using boto3 session
      allStacks = session.client("cloudformation").list_stacks()
      # Log the loop for something to look at
      log.info("[awsStart | {}] Querying all stacks...".format(str(accountName)))
      # Variables
      # 2 lists one for stackNames and other for its status.
      # To successfully exit this function, all stacks in these arrays have to be 'CREATE_COMPLETE'
      stackNames = []
      stackStatuses = []
      # Counter incremented when a stack finished successfully. Compared with list of stackNames in order to exit the function.
      completeStackStatusCounter = 0
      # Loop through all the stacks in 'allStacks'
      for stack in allStacks['StackSummaries']:
        if((stack['StackStatus'] == 'CREATE_IN_PROGRESS') or (stack['StackStatus'] == 'CREATE_COMPLETE') or (stack['StackStatus'] == 'CREATE_FAILED') or (stack['StackStatus'] == 'ROLLBACK_IN_PROGRESS') or (stack['StackStatus'] == 'ROLLBACK_FAILED') or (stack['StackStatus'] == 'ROLLBACK_COMPLETE')):
          stackNames.append(str(stack['StackName']))
          stackStatuses.append(str(stack['StackStatus']))
      # Add +1 to the 'completeStackStatusCounter' when a stack has status of 'CREATE_COMPLETE'
      for stackStatus in stackStatuses:
        # stack success
        if(stackStatus == 'CREATE_COMPLETE'):
          completeStackStatusCounter += 1
        # stack fail, set the fail flag and break the loop. It's over, a stack failed to deploy
        elif((stackStatus == 'CREATE_FAILED') or (stackStatus == 'ROLLBACK_IN_PROGRESS') or (stackStatus == 'ROLLBACK_FAILED') or (stackStatus == 'ROLLBACK_COMPLETE')):
          # mark the fail flag true
          failFlag = True
          # DBConnect ============================
          # Update task['errorInfo']
          DBConnect.appendTaskErrorInfo(taskId, accountName, "CloudFormation for {} failed to deploy. Log in with Admin and inspect the cloudFormation events.".format(str(accountName)))
          # Update task['taskStatus']
          DBConnect.setTaskStatusToError(taskId)
          # ======================================
          break
      # Check if all stacks are up successfully
      if(completeStackStatusCounter == len(stackNames)):
        # logging
        log.info("[awsStart | {}] Stacks created.".format(str(accountName)))
        # this will be False, no fail or error
        # Exit function
        return failFlag
      # Add to the timeout counter
      timeoutCounter += 1
      # Check for timeout, exit function if true
      if(timeoutCounter > 60):
        # logging
        log.error("[awsStart | {}] 60 minute timeout in queryAllStacks method, Timeout error.".format(str(accountName)))
        # mark the fail flag true
        failFlag = True
      # Check if the failFlag is set, if it is, a stack didn't deploy
      if(failFlag):
        # logging
        log.error("[awsStart | {}] Failed to create stack.".format(str(accountName)))
        # this will be True, some error occured or cloudFormation failed to deploy
        return failFlag
      # Sleep and give time for stacks to deploy
      time.sleep(60)
  except Exception as e:
    log.exception("[awsStart | {}] Query All Stacks function failed: {}.".format(str(accountName), str(e)))
    return True

# beautiful function ;D
def convertMonthIntToSrt(month):
  try:
    if(month == 1):
      return("Jan")
    elif(month == 2):
      return("Feb")
    elif(month == 3):
      return("Mar")
    elif(month == 4):
      return("Apr")
    elif(month == 5):
      return("May")
    elif(month == 6):
      return("Jun")
    elif(month == 7):
      return("Jul")
    elif(month == 8):
      return("Aug")
    elif(month == 9):
      return("Sep")
    elif(month == 10):
      return("Oct")
    elif(month == 11):
      return("Nov")
    elif(month == 12):
      return("Dec")
    else:
      return("Sensor")
  except:
    return("Sensor")

def addStackSuccessInfoToTask(session, taskId, accountName, successInfoToAppendToTask):
  # DBConnect ============================
  # Update task['successInfo']
  DBConnect.appendTaskSuccessInfo(taskId, accountName, successInfoToAppendToTask)
  # ======================================
  return

def queryStackAndReturnInfo(session, taskId, accountName, log):
  response = session.client("cloudformation").describe_stacks()
  for item in response['Stacks']:
    for i in item:
      if(i == 'Outputs'):
        # return the output info
        infoToPassIn = item[i]
        return infoToPassIn

# Return a plugin response from a plugin named in 'paramFile' variable
def sensorParameterPluginStatic(paramFile, paramValue, lab, region):
  # # convert the paramFile str to a runnable module
  pluginNameModule = import_module(str(paramFile))
  # get the processed response Value from the plugin
  pluginResponse = pluginNameModule.getIdentifier(lab, region, paramValue)
  # converting the str variable into a dict
  pluginResponseInJson = json.loads(str(pluginResponse))
  return pluginResponseInJson

def checkParamValueForError(paramValue):
  if(paramValue == "error"):
    return True
  return False

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.authorize_security_group_ingress
def addProtocolAllToSensorUSMServicesSG(session, accountName, log):
  SensorUSMServicesSG = ""
  try:
    # ----------------------------------------------
    # Get the "Sensor-USM-ServicesSG" security group
    # ----------------------------------------------
    # Get all security groups
    securityGroupsRaw = session.client("ec2").describe_security_groups()
    # Filter for the "Sensor-USM-ServicesSG" security group
    for securityGroup in securityGroupsRaw['SecurityGroups']:
      if("Sensor-USMServicesSG" in securityGroup['GroupName']):
        SensorUSMServicesSG = securityGroup['GroupId']
        break
    # --------------------------------
    # Authorize Security Group Ingress
    # --------------------------------
    response = session.client("ec2").authorize_security_group_ingress(CidrIp='192.168.250.0/24', GroupId=str(SensorUSMServicesSG), IpProtocol='-1')
    log.info("[awsStart | {}] Success authorizing security group ingress for seccurity group: '{}'. Boto3 response: {}".format(str(accountName), str(SensorUSMServicesSG), str(response)))
    # Return
    failFlag = False
    return [failFlag, "N/A"]
  except Exception as e:
    log.error("[awsStart | {}] Failed to add --protocol all to Sensor-USM-ServicesSG. Error: {}".format(str(accountName), str(e)))
    # Return
    failFlag = True
    return [failFlag, str(e)]

# https://stackoverflow.com/questions/48072398/get-list-of-ec2-instances-with-specific-tag-and-value-in-boto3
# https://stackoverflow.com/questions/38122563/filter-instances-by-state-with-boto3
# https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstances.html
def appendInternalAndExternalIpsForSuccessInfo(session, successInfoToAppendToTask, accountName, log):
  successInfoToAppendToTaskBackup = successInfoToAppendToTask
  try:
    publicIpAddress = ""
    privateIpAddress = ""

    # Need to filter for 'instance-state-name' because response may return many instances, some terminated without IP's.
    custom_filter = [ { 'Name':'tag:Name', 'Values': ['Sensor'] }, { 'Name':'instance-state-name', 'Values': ['running'] } ]

    response = session.client("ec2").describe_instances(Filters=custom_filter)

    # Will always be 1 sensor (1 instance from 'response' and custom_filter above)
    for i in response['Reservations']:
      for j in i['Instances']:
        publicIpAddress = j['PublicIpAddress']
        privateIpAddress = j['PrivateIpAddress']
        break

    successInfoToAppendToTask.append({'OutputKey': 'Sensor Public Ip', 'OutputValue': publicIpAddress})
    successInfoToAppendToTask.append({'OutputKey': 'Sensor Private Ip', 'OutputValue': privateIpAddress})

    log.info("[awsStart | {}] Appended Internal and External Sensor IP's to successInfo.".format(str(accountName)))
    return successInfoToAppendToTask
  except Exception as e:
    log.exception("[awsStart | {}] Failed to append Internal and External Sensor IP's to successInfo. Error: {}".format(str(accountName), str(e)))
    return successInfoToAppendToTaskBackup