#!/usr/bin/python3
# -*- coding: utf-8 -*-

# --------------------------------------------
# Jaroslaw Glodowski
# version: 1.0
# awsCreateAdmin.py - 2019/07/19
# --------------------------------------------

import boto3, logging, json

def createAdmin(jsonDoc):
  # ----------------------------------------------------------------------------------------------------------------------

  # Logger setup
  try:
    logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
    log = logging.getLogger('awsCreateAdmin')
  except Exception as e:
    # Logging* just print, can't log
    errorExceptionInfo = "[awsCreateAdmin | {}] Critical Logger Setup Error: {}".format(str(e))
    print(errorExceptionInfo)
    # Exit
    return errorExceptionInfo
  # ----------------------------------------------------------------------------------------------------------------------

  # Extract the info form jsonDoc
  try:
    accountName = jsonDoc['labName']
    userName = jsonDoc['userName']
    groupName = jsonDoc['groupName']
    password = jsonDoc['password']
    region = jsonDoc['region']
    adminPolicyJson = jsonDoc['adminPolicyJson']
    adminPolicyName = jsonDoc['adminPolicyName']
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsCreateAdmin] Critical Error Extracting 'jsonDoc' Parameters: {}".format(str(e))
    log.exception(errorExceptionInfo)
    # Exit
    return { "error" : str(errorExceptionInfo) }
  # ----------------------------------------------------------------------------------------------------------------------

  # boto3 setup
  try:
    session = boto3.Session(profile_name = accountName, region_name = region)
    log.info("[awsCreateAdmin | {}] Created boto3 session for: {} - {}".format(str(accountName), str(accountName), str(region)))
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsCreateAdmin | {}] Error creating the boto3 session: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # Exit
    return { "error" : str(errorExceptionInfo) }
  # ----------------------------------------------------------------------------------------------------------------------

  # Create a new user
  response = createNewUser(session, userName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsCreateAdmin | {}] Created a new User: {}".format(str(accountName), str(userName)))

  # Create a new group
  response = createNewGroup(session, groupName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsCreateAdmin | {}] Created a new Group: {}".format(str(accountName), str(groupName)))

  # Add the new user to the new group
  response = addUserToGroup(session, userName, groupName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsCreateAdmin | {}] Added User: {} to Group: {}".format(str(accountName), str(userName), str(groupName)))

  # Creating the admin policy
  response = createAdminPolicy(session, adminPolicyJson, adminPolicyName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  adminPolicyArn = response[2]
  log.info("[awsCreateAdmin | {}] Created a new Policy: {} Policy Arn: {}".format(str(accountName), str(adminPolicyName), str(adminPolicyArn)))

  # Attach policy to user
  response = attachPolicyToUser(session, userName, adminPolicyArn, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsCreateAdmin | {}] Attached Policy: {} to User: {}".format(str(accountName), str(adminPolicyName), str(userName)))

  # Give the user a login password
  response = createloginProfile(session, userName, password, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsCreateAdmin | {}] Created a Login Profile for User: {}".format(str(accountName), str(userName)))

  # ----------------------------------------------------------------------------------------------------------------------
  # Success after all of the above is done
  return { "success" : "Created an admin user for {}.  Account: {}  Username: {}  Password: {}".format(str(accountName), str(accountName).lower(), str(userName), str(password)) }
  # ----------------------------------------------------------------------------------------------------------------------

# -----------------
# Create a new user
# -----------------
def createNewUser(session, userName, accountName):
  try:
    # Create the user
    session.client("iam").create_user(UserName = str(userName))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Error message
    errorExceptionInfo = "[awsCreateAdmin | {}] Error creating new user: {}".format(str(accountName), str(e))
    # Return
    return[False, errorExceptionInfo]

# ------------------
# Create a new group
# ------------------
def createNewGroup(session, groupName, accountName):
  try:
    # Create the group
    session.client("iam").create_group(GroupName = str(groupName))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Error message
    errorExceptionInfo = "[awsCreateAdmin | {}] Error creating new group: {}".format(str(accountName), str(e))
    # Return
    return[False, errorExceptionInfo]

# -----------------
# Add user to group
# -----------------
def addUserToGroup(session, userName, groupName, accountName):
  try:
    # Create the group
    session.client("iam").add_user_to_group(UserName = str(userName), GroupName = str(groupName))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Error message
    errorExceptionInfo = "[awsCreateAdmin | {}] Error adding user to group: {}".format(str(accountName), str(e))
    # Return
    return[False, errorExceptionInfo]

# --------------------
# Creating AdminPolicy
# --------------------
def createAdminPolicy(session, adminPolicyJson, adminPolicyName, accountName):
  try:
    # Open the JSON file and store it as a JSON
    f = open(adminPolicyJson, "r")
    policyAsString = f.read()
    policyAsJson = json.loads(policyAsString)
    f.close()

    # Create the managed policy
    response = session.client("iam").create_policy(PolicyName = str(adminPolicyName), PolicyDocument = json.dumps(policyAsJson))
    # Extract the policy arn and return it index[2] for it to be passed into def attachPolicyToUser
    policyArn = response['Policy']['Arn']

    # Return
    return[True, "N/A", str(policyArn)]
  except Exception as e:
    # Error message
    errorExceptionInfo = "[awsCreateAdmin | {}] Error creating Admin Policy: {}".format(str(accountName), str(e))
    # Return
    return[False, errorExceptionInfo, "N/A"]

# ---------------------
# Attach policy to user
# ---------------------
def attachPolicyToUser(session, userName, adminPolicyArn, accountName):
  try:
    # Create the group
    session.client("iam").attach_user_policy(UserName = str(userName), PolicyArn = str(adminPolicyArn))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Error message
    errorExceptionInfo = "[awsCreateAdmin | {}] Error attaching policy to user: {}".format(str(accountName), str(e))
    # Return
    return[False, errorExceptionInfo]

# --------------------
# Create login Profile
# --------------------
def createloginProfile(session, userName, password, accountName):
  try:
    # Create the group
    session.client("iam").create_login_profile(UserName = str(userName), Password = str(password))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Error message
    errorExceptionInfo = "[awsCreateAdmin | {}] Error creating user login profile: {}".format(str(accountName), str(e))
    # Return
    return[False, errorExceptionInfo]
