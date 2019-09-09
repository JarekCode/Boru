#!/usr/bin/python3
# -*- coding: utf-8 -*-

# --------------------------------------------
# Jaroslaw Glodowski
# version: 1.0
# awsRemoveAdmin.py - 2019/07/25
# --------------------------------------------

import boto3, logging, json

def removeAdmin(jsonDoc):
  # ----------------------------------------------------------------------------------------------------------------------

  # Logger setup
  try:
    logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
    log = logging.getLogger('awsRemoveAdmin')
  except Exception as e:
    # Logging* just print, can't log
    errorExceptionInfo = "[awsRemoveAdmin | {}] Critical Logger Setup Error: {}".format(str(e))
    print(errorExceptionInfo)
    # Exit
    return errorExceptionInfo
  # ----------------------------------------------------------------------------------------------------------------------

  # Extract the info form jsonDoc
  try:
    accountName = jsonDoc['labName']
    userName = jsonDoc['userName']
    groupName = jsonDoc['groupName']
    region = jsonDoc['region']
    adminPolicyName = jsonDoc['adminPolicyName']
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsRemoveAdmin] Critical Error Extracting 'jsonDoc' Parameters: {}".format(str(e))
    log.exception(errorExceptionInfo)
    # Exit
    return { "error" : str(errorExceptionInfo) }
  # ----------------------------------------------------------------------------------------------------------------------

  # boto3 setup
  try:
    session = boto3.Session(profile_name = accountName, region_name = region)
    log.info("[awsRemoveAdmin | {}] Created boto3 session for: {} - {}".format(str(accountName), str(accountName), str(region)))
  except Exception as e:
    # Logging
    errorExceptionInfo = "[awsRemoveAdmin | {}] Error creating the boto3 session: {}".format(str(accountName), str(e))
    log.exception(errorExceptionInfo)
    # Exit
    return { "error" : str(errorExceptionInfo) }
  # ----------------------------------------------------------------------------------------------------------------------

  # Delete the Policy
  log.info("[awsRemoveAdmin | {}] Deleting Policy: {}...".format(str(accountName), str(adminPolicyName)))
  response = deletePolicy(session, adminPolicyName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsRemoveAdmin | {}] Deleted Policy: {}".format(str(accountName), str(adminPolicyName)))
  # ----------------------------------------------------------------------------------------------------------------------

  # Remove User from Group
  response = removeUserFromGroup(session, userName, groupName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsRemoveAdmin | {}] Removed User: {} from Group: {}".format(str(accountName), str(userName), str(groupName)))
  # ----------------------------------------------------------------------------------------------------------------------

  # Delete the Group
  response = deleteGroup(session, groupName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsRemoveAdmin | {}] Deleted Group: {}".format(str(accountName), str(groupName)))
  # ----------------------------------------------------------------------------------------------------------------------

  # Remove User login profile
  response = removeUserLoginProfile(session, userName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsRemoveAdmin | {}] Removed login profile from User: {}".format(str(accountName), str(userName)))
  # ----------------------------------------------------------------------------------------------------------------------

  # Delete the User
  response = deleteUser(session, userName, accountName)
  if(not response[0]):
    # Logging
    log.exception(response[1])
    return { "error" : str(response[1]) }
  log.info("[awsRemoveAdmin | {}] Deleted User: {}".format(str(accountName), str(userName)))
  # ----------------------------------------------------------------------------------------------------------------------

  # ----------------------------------------------------------------------------------------------------------------------
  # Success after all of the above is done
  return { "success" : "Deleted {} from {}".format(str(userName), str(accountName)) }
  # ----------------------------------------------------------------------------------------------------------------------

# -------------
# Delete Policy
# -------------
# Before you can delete a managed policy, you must first detach the policy from all users, groups, and roles that it is attached to.
# In addition, you must delete all the policy's versions.
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.delete_policy
def deletePolicy(session, adminPolicyName, accountName):
  try:
    # 1. Get the Admin Policy Arn based on the Admin Policy Name
    adminPolicyArn = ""
    allPolicies = session.client("iam").list_policies()
    for policy in allPolicies['Policies']:
      if(policy['PolicyName'] == str(adminPolicyName)):
        adminPolicyArn = policy['Arn']
        break
    # If it does not exist, Return from function
    if(not adminPolicyArn):
      return[True, "N/A"]

    # 2. Detach policy from all users
    allUsers = session.client("iam").list_users()
    for user in allUsers['Users']:
      try:
        session.client("iam").detach_user_policy(UserName = str(user['UserName']), PolicyArn = str(adminPolicyArn))
      except Exception as e:
        # Ignore NoSuchEntity
        if("NoSuchEntity" in str(e)):
          pass
        else:
          return[False, str(e)]

    # 3. Detach policy from all groups
    allGroups = session.client("iam").list_groups()
    for group in allGroups['Groups']:
      try:
        session.client("iam").detach_group_policy(GroupName = str(group['GroupName']), PolicyArn = str(adminPolicyArn))
      except Exception as e:
        # Ignore NoSuchEntity
        if("NoSuchEntity" in str(e)):
          pass
        else:
          return[False, str(e)]

    # 4. Detach policy from all roles
    allRoles = session.client("iam").list_roles()
    for role in allRoles['Roles']:
      try:
        session.client("iam").detach_role_policy(RoleName = str(role['RoleName']), PolicyArn = str(adminPolicyArn))
      except Exception as e:
        # Ignore UnmodifiableEntity or NoSuchEntity
        if("UnmodifiableEntity" in str(e) or "NoSuchEntity" in str(e)):
          pass
        else:
          return[False, str(e)]

    # 5. Delete all the policy's versions
    allPolicysVersions = session.client("iam").list_policy_versions(PolicyArn = str(adminPolicyArn))
    for policyVersion in allPolicysVersions['Versions']:
      try:
        session.client("iam").delete_policy_version(PolicyArn = str(adminPolicyArn), VersionId = str(policyVersion['VersionId']))
      except Exception as e:
        # Ignore DeleteConflict (Cannot delete the default version of a policy)
        if("DeleteConflict" in str(e)):
          pass
        else:
          return[False, str(e)]

    # 6. Delete the policy
    session.client("iam").delete_policy(PolicyArn = str(adminPolicyArn))

    # Return
    return[True, "N/A"]
  except Exception as e:
    # Error message
    errorExceptionInfo = "[awsRemoveAdmin | {}] Error deleting policy: {}".format(str(accountName), str(e))
    # Return
    return[False, errorExceptionInfo]

# ----------------------
# Remove User From Group
# ----------------------
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.remove_user_from_group
def removeUserFromGroup(session, userName, groupName, accountName):
  try:
    # Remove the user from the group
    session.client("iam").remove_user_from_group(GroupName = str(groupName), UserName = str(userName))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Ignore NoSuchEntity (No User)
    if("NoSuchEntity" in str(e)):
      return[True, "N/A"]
    else:
      # Error message
      errorExceptionInfo = "[awsRemoveAdmin | {}] Error removing user from group: {}".format(str(accountName), str(e))
      # Return
      return[False, errorExceptionInfo]

# ------------
# Delete Group
# ------------
# The group must not contain any users or have any attached policies. (Done in deletePolicy() and removeUserFromGroup() above)
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.delete_group
def deleteGroup(session, groupName, accountName):
  try:
    # Delete the group
    session.client("iam").delete_group(GroupName = str(groupName))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Ignore NoSuchEntity (No Group)
    if("NoSuchEntity" in str(e)):
      return[True, "N/A"]
    else:
      # Error message
      errorExceptionInfo = "[awsRemoveAdmin | {}] Error deleting group: {}".format(str(accountName), str(e))
      # Return
      return[False, errorExceptionInfo]

# -------------------------
# Remove User Login Profile
# -------------------------
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.delete_login_profile
def removeUserLoginProfile(session, userName, accountName):
  try:
    # Delete user login profile
    session.client("iam").delete_login_profile(UserName = str(userName))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Ignore NoSuchEntity (No User)
    if("NoSuchEntity" in str(e)):
      return[True, "N/A"]
    else:
      # Error message
      errorExceptionInfo = "[awsRemoveAdmin | {}] Error deleting user login profile: {}".format(str(accountName), str(e))
      # Return
      return[False, errorExceptionInfo]

# -----------
# Delete User
# -----------
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html#IAM.Client.delete_user
def deleteUser(session, userName, accountName):
  try:
    # Delete the user
    session.client("iam").delete_user(UserName = str(userName))
    # Return
    return[True, "N/A"]
  except Exception as e:
    # Ignore NoSuchEntity (No User)
    if("NoSuchEntity" in str(e)):
      return[True, "N/A"]
    else:
      # Error message
      errorExceptionInfo = "[awsRemoveAdmin | {}] Error deleting user: {}".format(str(accountName), str(e))
      # Return
      return[False, errorExceptionInfo]

# ----------------------------------------------------------------------------------------------------------------------------------------------------
# TESTING ------- TESTING ------- TESTING ------- TESTING ------- TESTING------- TESTING ------- TESTING------- TESTING ------- TESTING------- TESTING
# ----------------------------------------------------------------------------------------------------------------------------------------------------
#jsonDoc = {"labName" : "Student01", "userName" : "Admin", "groupName" : "Admin", "region" : "us-east-1", "adminPolicyName" : "AdminPolicyBoru"}
#removeAdmin(jsonDoc)
# ----------------------------------------------------------------------------------------------------------------------------------------------------
# TESTING ------- TESTING ------- TESTING ------- TESTING ------- TESTING------- TESTING ------- TESTING------- TESTING ------- TESTING------- TESTING
# ----------------------------------------------------------------------------------------------------------------------------------------------------