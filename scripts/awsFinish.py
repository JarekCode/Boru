#!/usr/bin/python3
# -*- coding: utf-8 -*-

# --------------------------------------------
# Jaroslaw Glodowski
# version: 1.5
# awsFinish.py - Fixed issue with .remove() skipping some key-pairs etc.
# --------------------------------------------

import boto3, json, time, logging
# used for updating task status, in .update_one, ObjectId is needed not a str
from bson import ObjectId
# Adding a path for the DBConnect in /opt/boru/
import sys
# Required for the DBConnect
sys.path.append("../")
# /opt/boru/DBConnect.py
import DBConnect

# ---------
# labFinish
# ---------
def main(jsonDoc):

  # the big fail flag, set whenever some error occurs. It is looked at at the very end, and based on that, the flag is set.
  # whenever the flag is set, errorInfo is appended to the job.

  # The reason the list is a pointer is because there is no need for a return in the methond.
  # If the list will stay empy to the end, no errors. If anything gets appended to the list, this means something went wrong and the
  # finish script didn't run fully/successfully
  failFlag = []

  accountName = jsonDoc["lab"]
  taskId = jsonDoc['task_id']

  # logging setup
  logging.basicConfig(filename='/var/log/boru.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(message)s')
  # new run message of awsFinish
  logging.info("[awsFinish | {}] ----------------------------".format(str(accountName)))
  logging.info("[awsFinish | {}] ------ NEW FINISH RUN ------".format(str(accountName)))
  logging.info("[awsFinish | {}] ----------------------------".format(str(accountName)))

  # -------------------
  # labFinish Variables
  # -------------------

  # creating the session for the 'Student' lab
  mySession = boto3.Session(profile_name = accountName)

  logging.info("[awsFinish | {}] Session created!".format(str(accountName)))

  # list of all regions to loop through
  listOfRegions = []

  # getting a list of regions into 'listOfRegions' array
  listOfRegions = mySession.get_available_regions(service_name = "ec2")

  logging.info("[awsFinish | {}] Regions gathered!".format(str(accountName)))

  # for every region do the following:
  for currentRegion in listOfRegions:

    # create a session for that region
    session = boto3.Session(profile_name = accountName, region_name = currentRegion)

    # print the region name on the screen
    ##print("\n-----")
    ##print(currentRegion)
    ##print("-----")
    # add the region to logging
    logging.info("[awsFinish | {}] -------".format(str(accountName)))
    logging.info("[awsFinish | {}] Region: {}".format(str(accountName), str(currentRegion)))
    logging.info("[awsFinish | {}] -------".format(str(accountName)))

    # create a session resource used to work with buckets
    s3ForDeletingBucket = session.resource('s3')

    # ----------------
    # Region Variables
    # ----------------

    # list of all the 'users' extracted from the 'users'
    listOfUsers = []
    # list of all the 'groups' extracted from the 'groups'
    listOfGroups = []
    # list of all the 'roles' extracted from the 'roles'
    listOfRoles = []
    # list of 'roles' not to delete
    whiteListedRoles = ["AWSServiceRoleForAmazonGuardDuty", "AWSServiceRoleForOrganizations", "OrganizationAccountAccessRole", "ReadOnlyRoleWithCloudTrailManagement", "AWSServiceRoleForSupport", "AWSServiceRoleForTrustedAdvisor"]
    # list of 'group inline policies'
    listOfGroupInlinePoliciesNames = []
    # list of 'group managed policies' ('attached' in boto3 function calls)
    listOfGroupManagedPoliciesARNs = []
    # list of all 'instances IDs' extracted from 'instances'
    listOfInstancesIds = []
    # list of all 'key pairs' extracted from 'keyPairs'
    listOfKeyPairs = []
    # list of 'buckets' extracted from 'buckets'
    listOfBuckets = []
    # list of 'cloud formation stacks' extracted from 'cloudFormationStacks'
    listOfCloudFormationStacks = []
    # list of 'cloud trails' extracted from 'cloudTrails'
    listOfCloudTrails = []
    # list of 'flow log IDs' extracted from 'flowLogs'
    listOfFlowLogIds = []
    # list of 'cloud watch log groups' extracted from 'cloudWatchLogGroups'
    listOfCloudWatchLogGroups = []


    # --------------
    # Gathering Data
    # --------------
    # List of 'Roles' NOT to delete
    logging.info("[awsFinish | {}] White Listed Roles: {}".format(str(accountName), str(whiteListedRoles)))
    logging.info("[awsFinish | {}] Gathering Data...".format(str(accountName)))
    ##print("\n--- Gathering Data ---\n")

    # getting all 'Users'
    logging.info("[awsFinish | {}] Getting all users...".format(str(accountName)))
    getAllUsers(session, listOfUsers)
    ##logging.info("Variable listOfUsers: {}".format(listOfUsers))

    # getting all 'Groups'
    logging.info("[awsFinish | {}] Getting all groups...".format(str(accountName)))
    getAllGroups(session, listOfGroups)
    ##logging.info("Variable listOfGroups: {}".format(listOfGroups))

    # getting all 'Roles'
    logging.info("[awsFinish | {}] Getting all roles...".format(str(accountName)))
    getAllRoles(session, listOfRoles)
    ##logging.info("Variable listOfRoles: {}".format(listOfRoles))

    # getting all 'Inline Policies' for each 'group'
    logging.info("[awsFinish | {}] Getting all group inline policies...".format(str(accountName)))
    getGroupInlinePolicies(session, listOfGroups, listOfGroupInlinePoliciesNames)
    ##logging.info("Variable listOfGroupInlinePoliciesNames: {}".format(listOfGroupInlinePoliciesNames))

    # getting all 'Managed Policies' for each 'group'
    logging.info("[awsFinish | {}] Getting all group managed policies...".format(str(accountName)))
    getGroupManagedPolicies(session, listOfGroups, listOfGroupManagedPoliciesARNs)
    ##logging.info("Variable listOfGroupManagedPoliciesARNs: {}".format(listOfGroupManagedPoliciesARNs))

    # getting and appending all 'EC2 Instances ID's' to 'listOfInstancesIds'
    logging.info("[awsFinish | {}] Getting all EC2 instances...".format(str(accountName)))
    getAllEc2Instances(session, listOfInstancesIds)
    ##logging.info("Variable listOfInstancesIds: {}".format(listOfInstancesIds))

    # getting and appending all 'Key-Pairs' into 'listOfKeyPairs'
    logging.info("[awsFinish | {}] Getting all key pairs...".format(str(accountName)))
    getAllKeyPairs(session, listOfKeyPairs)
    logging.info("[awsFinish | {}] Variable listOfKeyPairs: {}".format(str(accountName), listOfKeyPairs))

    # getting and appending all 'Buckets' into 'listOfBuckets'
    logging.info("[awsFinish | {}] Getting all buckets...".format(str(accountName)))
    getAllBuckets(session, listOfBuckets)
    ##logging.info("Variable listOfBuckets: {}".format(listOfBuckets))

    # getting and appending all 'Cloud Formation Stacks' into 'listOfCloudFormationStacks'
    logging.info("[awsFinish | {}] Getting all cloudFormation stacks...".format(str(accountName)))
    getAllCloudFormationStacks(session, listOfCloudFormationStacks)
    ##logging.info("Variable listOfCloudFormationStacks: {}".format(listOfCloudFormationStacks))

    # getting and appending all 'Cloud Trails' into 'listOfCloudTrails'
    logging.info("[awsFinish | {}] Getting all cloud trails...".format(str(accountName)))
    getAllCloudTrails(session, listOfCloudTrails)
    ##logging.info("Variable listOfCloudTrails: {}".format(listOfCloudTrails))

    # getting and appending all 'Flow Logs' into 'listOfFlowLogIds'
    logging.info("[awsFinish | {}] Getting all flow logs...".format(str(accountName)))
    getAllFlowLogs(session, listOfFlowLogIds)
    ##logging.info("Variable listOfFlowLogIds: {}".format(listOfFlowLogIds))

    # getting and appending all 'Cloud Watch Log Groups' into 'listOfCloudWatchLogGroups'
    logging.info("[awsFinish | {}] Getting all cloudWatch log groups...".format(str(accountName)))
    getAllCloudWatchLogGroups(session, listOfCloudWatchLogGroups)
    ##logging.info("Variable listOfCloudWatchLogGroups: {}".format(listOfCloudWatchLogGroups))

    # -------------------------
    # Deleting all Elastic IP's
    # -------------------------
    # delete all elastic ip's
    logging.info("[awsFinish | {}] Deleting all Elastic IP's...".format(str(accountName)))
    findAndDeleteAllElasticIPs(session, taskId, failFlag, accountName, logging)

    # -------------------
    # deleting all groups
    # -------------------
    # only do if there is at least one group
    if(listOfGroups):
      logging.info("[awsFinish | {}] Deleting Groups...".format(str(accountName)))
      # Removing all Users from all Groups
      logging.info("[awsFinish | {}] Removing all users from all groups...".format(str(accountName)))
      removeAllUsersFromAllGroups(session, listOfUsers, listOfGroups, logging, accountName, taskId, failFlag)
      # Deleting all Inline Policies for all Groups
      logging.info("[awsFinish | {}] Deleting all group inline policies...".format(str(accountName)))
      deleteGroupInlinePolicies(session, listOfGroups, listOfGroupInlinePoliciesNames, logging, accountName, taskId, failFlag)
      # Deleting all Managed Policies for all Groups
      logging.info("[awsFinish | {}] Deleting all group managed policies...".format(str(accountName)))
      deleteGroupManagedPolicies(session, listOfGroups, listOfGroupManagedPoliciesARNs, listOfUsers, logging, accountName, taskId, failFlag)
      # Deleting all Groups
      logging.info("[awsFinish | {}] Deleting all groups...".format(str(accountName)))
      deleteAllGroups(session, listOfGroups, logging, accountName, taskId, failFlag)
    else:
      logging.info("[awsFinish | {}] No Groups found.".format(str(accountName)))


    # -----------------------------------------
    # deleting all local scope managed policies
    # -----------------------------------------
    deleteLocalScopeManagedPolicies(session, logging, accountName, taskId, failFlag, listOfGroups, listOfUsers, listOfRoles, whiteListedRoles)

    # ------------------
    # deleting all users
    # ------------------
    # only do if there is at least one user
    if(listOfUsers):
      # Deleting all dependencies from all Users: Access Keys, Signing Certificates, MFA Devices, User Inline Policies, User Managed Policies
      logging.info("[awsFinish | {}] Deleting all dependencies from all users...".format(str(accountName)))
      deleteAllDependenciesFromAllUsers(session, listOfUsers, logging, accountName, taskId, failFlag)
      # Deleting all Users
      logging.info("[awsFinish | {}] Deleting all users...".format(str(accountName)))
      deleteAllUsers(session, listOfUsers, logging, accountName, taskId, failFlag)
    else:
      ##print("\nNo Users found.")
      logging.info("[awsFinish | {}] No Users found.".format(str(accountName)))

    # -----------------------------
    # terminating all ec2 instances
    # -----------------------------
    # only do if there is at least one ec2 instance
    if(listOfInstancesIds):
      # Disabling Termination Protection from all EC2 Instances from listOfInstancesIds
      logging.info("[awsFinish | {}] Disabling termination protection from all EC2 instances...".format(str(accountName)))
      disableTerminationProtectionForAllEc2Instances(session, listOfInstancesIds, logging, accountName, taskId, failFlag)
      # Terminating all EC2 Instances from listOfInstancesIds
      logging.info("[awsFinish | {}] Deleting all users...".format(str(accountName)))
      terminateAllEc2Instances(session, listOfInstancesIds, logging, accountName, taskId, failFlag)
    else:
      logging.info("[awsFinish | {}] No EC2 Instances found.".format(str(accountName)))

    # --------------------------
    # deleting all the key pairs
    # --------------------------
    # only do if there is at least one key pair
    if(listOfKeyPairs):
      # Deleting all Key-Pairs form listOfKeyPairs
      logging.info("[awsFinish | {}] Deleting all key pairs...".format(str(accountName)))
      deleteAllKeyPairs(session, listOfKeyPairs, logging, accountName, taskId, failFlag)
    else:
      logging.info("[awsFinish | {}] No Key Pairs found.".format(str(accountName)))

    # --------------------
    # deleting all buckets
    # --------------------
    # only do if there is at least one bucket
    if(listOfBuckets):
      # BEFORE DELETING A BUCKET: All objects (including all object versions and Delete Markers) in the bucket must be deleted before the bucket itself can be deleted
      # https://stackoverflow.com/questions/43326493/what-is-the-fastest-way-to-empty-s3-bucket-using-boto3
      deletingAllBuckets(session, s3ForDeletingBucket, listOfBuckets, logging, accountName, taskId, failFlag)
    else:
      logging.info("[awsFinish | {}] No Buckets found.".format(str(accountName)))


    # #IGNORING BECAUSE OF THE AWS BUCKET ERROR

    # # -----------------------------------
    # # checking if all buckets are deleted
    # # -----------------------------------
    # # getting and appending all 'Buckets' into 'listOfBuckets'
    # logging.info("[awsFinish | {}] Getting all buckets...".format(str(accountName)))
    # getAllBuckets(session, listOfBuckets)

    # # Check at the end if any buckets are left, if so: add error to the awsFinish script
    # if(listOfBuckets):
    #   # logging
    #   errorExceptionInfo = "[awsFinish | {}] Failed to delete Bucket(s). Bucket(s) left: {}".format(accountName, str(listOfBuckets))
    #   logging.error(errorExceptionInfo)
    #   # DBConnect ============================
    #   # Update task['errorInfo']
    #   DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    #   # ======================================
    #   failFlag.append("Error: {}".format(errorExceptionInfo))


    # -------------------------------
    # deleting cloud formation stacks
    # -------------------------------
    # only do if there is at least one cloud formation stack
    if(listOfCloudFormationStacks):
      # delete all cloud formatio stacks form listOfCloudFormationStacks
      logging.info("[awsFinish | {}] Deleting all cloudFormation stacks...".format(str(accountName)))
      deleteAllCloudFormationStacks(session, listOfCloudFormationStacks, logging, accountName, taskId, failFlag)
    else:
      logging.info("[awsFinish | {}] No Cloud Formation Stacks found.".format(str(accountName)))

    # ---------------------
    # Deleting Cloud Trails
    # ---------------------
    # only do if there is at least one cloud trail
    if(listOfCloudTrails):
      # delete all cloud trails form listOfCloudTrails
      logging.info("[awsFinish | {}] Deleting all cloud trails...".format(str(accountName)))
      deleteAllCloudTrails(session, listOfCloudTrails, logging, accountName, taskId, failFlag)
    else:
      logging.info("[awsFinish | {}] No Cloud Trails found.".format(str(accountName)))

    # ----------------------
    # Deleting VPC Flow Logs
    # ----------------------
    # only do if there is at least one vpc flow log
    if(listOfFlowLogIds):
      # delete all flow logs from listOfFlowLogIds
      logging.info("[awsFinish | {}] Deleting all flow logs...".format(str(accountName)))
      deleteAllFlowLogs(session, listOfFlowLogIds, logging, accountName, taskId, failFlag)
    else:
      logging.info("[awsFinish | {}] No VPC Flow Logs found.".format(str(accountName)))

    # -------------------
    # Deleting Log Groups
    # -------------------
    # only do if there is at least one cloud watch log group
    if(listOfCloudWatchLogGroups):
      # delete all cloud watch log groups form listOfCloudWatchLogGroups
      logging.info("[awsFinish | {}] Deleting all cloud watch log groups...".format(str(accountName)))
      deleteAllCloudWatchLogGroups(session, listOfCloudWatchLogGroups, logging, accountName, taskId, failFlag)
    else:
      logging.info("[awsFinish | {}] No Cloud Watch Log Groups found.".format(str(accountName)))

    # ------------------------
    # Deleting Security Groups
    # ------------------------
    # delete all security groups
    logging.info("[awsFinish | {}] Deleting all security groups...".format(str(accountName)))
    deleteAllSecurityGroups(session, logging, accountName)

    # ------------------
    # Deleting all Roles
    # ------------------
    # delete all roles
    logging.info("[awsFinish | {}] Deleting all roles...".format(str(accountName)))
    deleteAllRoles(session, listOfRoles, whiteListedRoles, logging, accountName, taskId, failFlag)


    # list all the roles that are left (AWS Roles)
    # list of roles reset to none
    listOfRoles = []
    # getting all roles again
    getAllRoles(session, listOfRoles)
    # logging
    logging.info("[awsFinish | {}] listOfRoles Left: {}".format(str(accountName), str(listOfRoles)))


  # update task status to ready or error
  if(failFlag):
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, failFlag)
    # Update task['taskStatus']
    DBConnect.setTaskStatusToError(taskId)
    # ======================================
    # logging
    logging.info("[awsFinish | {}] labFinish Done.".format(str(accountName)))
  else:
    # DBConnect ============================
    # Update task['taskStatus']
    DBConnect.setTaskStatusToReady(taskId)
    # ======================================
    # logging
    logging.info("[awsFinish | {}] labFinish Done.".format(str(accountName)))

  # reset the failFlag
  failFlag = []

  # awsFinish Done

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# labFinish Functions
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# -------------
# Get all Users
# -------------
def getAllUsers(session, listOfUsers):
  # getting users
  # a dictionary extracted using 'list_users()'
  users = session.client("iam").list_users()
  # appdend each user to the list of users
  for user in users["Users"]:
    # append to list
    listOfUsers.append(user["UserName"])


# --------------
# Get all Groups
# --------------
def getAllGroups(session, listOfGroups):
  # getting groups
  # a dictionary extracted using 'list_groups()'
  groups = session.client("iam").list_groups()
  # appdend each group to the list of group
  for group in groups["Groups"]:
    # append to list
    listOfGroups.append(group["GroupName"])


# -------------
# Get all Roles
# -------------
def getAllRoles(session, listOfRoles):
  # getting roles
  # a dictionary extracted using list_roles()
  roles = session.client("iam").list_roles()
  # appdend each role to the list of roles
  for role in roles["Roles"]:
    # append to list
    listOfRoles.append(role["RoleName"])


# --------------------------------
# Remove All Users from All Groups
# --------------------------------
def removeAllUsersFromAllGroups(session, listOfUsers, listOfGroups, logging, accountName, taskId, failFlag):
  # removing all users from all groups
  # for every group
  for group in listOfGroups:
    # for every user
    for user in listOfUsers:
      try:
        # remove every user from that group
        session.client("iam").remove_user_from_group(GroupName = group, UserName = user)
        # logging
        logging.info("[awsFinish | {}] Removing User: '{}' From Group: '{}'".format(accountName, user, group))
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to Remove User: '{}' From Group: '{}'. Error: {}".format(accountName, user, group, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))


# -----------------------------
# Getting Group Inline Policies
# -----------------------------
def getGroupInlinePolicies(session, listOfGroups, listOfGroupInlinePoliciesNames):
  # getting all group inline policies
  # for each group
  for group in listOfGroups:
    # a dictionary extracted using list_group_policies()
    inlineGroupPolicies = session.client("iam").list_group_policies(GroupName=group)
    # buffer array to be appended at the end
    bufferInlineNames = []
    # add all the Inline Policies into a buffer array
    for inlinePolicy in inlineGroupPolicies["PolicyNames"]:
      # append to the buffer array
      bufferInlineNames.append(inlinePolicy)
    # append the buffer array to listOfGroupInlinePoliciesNames ([[...],[...],[...]])
    listOfGroupInlinePoliciesNames.append(bufferInlineNames)


# ------------------------------
# Getting Group Managed Policies
# ------------------------------
def getGroupManagedPolicies(session, listOfGroups, listOfGroupManagedPoliciesARNs):
  # getting all group managed policies
  # for each group
  for group in listOfGroups:
    # a dictionary extracted using list_attached_group_policies()
    managedGroupPolicies = session.client("iam").list_attached_group_policies(GroupName=group)
    # buffer array to be appended at the end
    bufferManagedARNs = []
    # for each managed policy("attached"), add Policy ARN into buffer array
    for managedPolicy in managedGroupPolicies["AttachedPolicies"]:
      # append to the buffer array
      bufferManagedARNs.append(managedPolicy["PolicyArn"])
    # appending the buffer array to listOfGroupManagedPoliciesARNs ([[...],[...],[...]])
    listOfGroupManagedPoliciesARNs.append(bufferManagedARNs)

# ------------------------------
# Deleting Group Inline Policies
# ------------------------------
def deleteGroupInlinePolicies(session, listOfGroups, listOfGroupInlinePoliciesNames, logging, accountName, taskId, failFlag):
  # deleting all group inline policies
  # deleting all policies for all groups, in future will change so only policies for a specific group are deleted, not just do it all for now
  # for every group
  for group in listOfGroups:
    # for every inline policy array
    for inlinePolicy in listOfGroupInlinePoliciesNames:
      # for every inline policy in the array of inline policies
      for policy in inlinePolicy:
        # not all inline policies will be in all groups, thats why try
        try:
          # delete policy from group
          session.client("iam").delete_group_policy(GroupName = group, PolicyName = policy)
          # logging
          logging.info("[awsFinish | {}] Deleting Group Inline Policy: '{}' For Group: '{}'".format(accountName, policy, group))
        # except the inline policy as it is not in the current group
        except Exception as e:
          if("NoSuchEntity" in str(e)):
            pass
          else:
            # logging
            errorExceptionInfo = "[awsFinish | {}] Did not find Inline Policy for group: '{}'".format(accountName, str(e))
            logging.exception(errorExceptionInfo)
            # DBConnect ============================
            # Update task['errorInfo']
            DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
            # ======================================
            failFlag.append("Error: {}".format(errorExceptionInfo))

# -------------------------------
# Deleting Group Managed Policies
# -------------------------------
# throws exception but deletes the deleted/detaches the Managed Policies
def deleteGroupManagedPolicies(session, listOfGroups, listOfGroupManagedPoliciesARNs, listOfUsers, logging, accountName, taskId, failFlag):
  # deleting all group managed policies
  # for each group
  for group in listOfGroups:
    # for each managed policy array
    for managedPolicy in listOfGroupManagedPoliciesARNs:
      # for each managed policy in that array do:
      for policyArn in managedPolicy:
        # array of managed policy versions to delete, can be empty
        arrayOfPolicyVersions = []
        # throws exception
        try:
          # detach the policy from group
          session.client("iam").detach_group_policy(GroupName = str(group), PolicyArn = str(policyArn))
          # logging
          logging.info("[awsFinish | {}] Detaching Group Managed Policy: '{}' From Group: '{}'".format(accountName, policyArn, group))
        except Exception as e:
          # logging
          errorExceptionInfo = "[awsFinish | {}] Failed to detach Group Managed Policy from group: {}".format(accountName, str(e))
          logging.exception(errorExceptionInfo)
          # DBConnect ============================
          # Update task['errorInfo']
          DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
          # ======================================
          failFlag.append("Error: {}".format(errorExceptionInfo))
        # for each user detach the managed policy
        for user in listOfUsers:
          # throws exception
          try:
            # detach the user from managed policy
            session.client("iam").detach_user_policy(UserName = str(user), PolicyArn = str(policyArn))
            # logging
            logging.info("[awsFinish | {}] Detaching User '{}' Inline Policy: '{}' For Group: '{}'".format(accountName, user, policy, group))
          except Exception as e:
            # logging
            errorExceptionInfo = "[awsFinish | {}] Failed to detach User from Group Managed Policy: {}".format(accountName, str(e))
            logging.exception(errorExceptionInfo)
            # DBConnect ============================
            # Update task['errorInfo']
            DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
            # ======================================
            failFlag.append("Error: {}".format(errorExceptionInfo))
        # get all the versions id of that policy in an array
        policyVersions = session.client("iam").list_policy_versions(PolicyArn = policyArn)
        # for each policy version found do:
        for policyVersion in policyVersions["Versions"]:
          # throws exception
          try:
            # append the policy version id to arrayOfPolicyVersions
            arrayOfPolicyVersions.append(policyVersion["VersionId"])
            # logging
            logging.info("[awsFinish | {}] Getting Managed Policy Versions: '{}' For Group: '{}'".format(accountName, policyVersion, group))
          except Exception as e:
            # logging
            logging.warning("[awsFinish | {}] No Manage Policy Version found: '{}'".format(accountName, str(e)))

        # Deleting all the versions of that policy
        # for each policy version in arrayOfPolicyVersions do:
        policyVersionsToRemove = []
        for policyVersionId in arrayOfPolicyVersions:
          # throws exception
          try:
            # delete the policy version
            ##print("Deleting Policy-Version(ARN):", policyVersionId, "from Policy(ARN):", policyArn, end=" ")
            session.client("iam").delete_policy_version(PolicyArn = policyArn, VersionId = policyVersionId)
            # delete the policy version id from arrayOfPolicyVersions
            policyVersionsToRemove.append(policyVersionId)
            # logging
            logging.info("Deleting Managed Policy Version: '{}' For Group: '{}'".format(policyVersionId, group))
          except Exception as e:
            ##print(str(e))
            # logging
            logging.warning("No Managed Policy Version found: {}".format(str(e)))
        # now remove the policy versions from the main array
        for i in policyVersionsToRemove:
          arrayOfPolicyVersions.remove(i)

        # throws exception
        try:
          # detaching the managed policy
          ##print("\nDetaching Policy(ARN):", policyArn, end=" ")
          session.client("iam").detach_group_policy(GroupName = group, PolicyArn = policyArn)
          # logging
          logging.info("Detaching Group Managed Policy(ARN): '{}'".format(policyArn))
        except Exception as e:
          # logging
          errorExceptionInfo = "Failed to detach Group Managed Policy: {}".format(str(e))
          logging.exception(errorExceptionInfo)
          # DBConnect ============================
          # Update task['errorInfo']
          DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
          # ======================================
          failFlag.append("Error: {}".format(errorExceptionInfo))


# -------------------
# Deleting All Groups
# -------------------
def deleteAllGroups(session, listOfGroups, logging, accountName, taskId, failFlag):
  # deleting all groups
  # for each group
  groupsToDelete = []
  for group in listOfGroups:
    # throws exception
    try:
      session.client("iam").delete_group(GroupName = group)
      # delete the group from listOfGroups
      groupsToDelete.append(group)
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to delete Group: '{}' Error:{}".format(accountName, group, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))
  # now remove all deleted groups from the main array
  for i in groupsToDelete:
    listOfGroups.remove(i)


# Deleting local scope managed policies
def deleteLocalScopeManagedPolicies(session, logging, accountName, taskId, failFlag, listOfGroups, listOfUsers, listOfRoles, whiteListedRoles):
  # lists of arns
  listOfArns = []

  # Get all local scope managed policies
  resp = session.client("iam").list_policies(Scope='Local')
  for i in resp['Policies']:
    listOfArns.append(str(i['Arn']))

  # Detache all the arns from all entities
  for policyArn in listOfArns:
    # 1 Detach from all users
    for user in listOfUsers:
      try:
        # detach the user from managed policy
        session.client("iam").detach_user_policy(UserName = str(user), PolicyArn = str(policyArn))
        # logging
        logging.info("[awsFinish | {}] Detached User: {} from Managed Local Policy: {}".format(accountName, user, policyArn))
      except Exception as e:
        if("NoSuchEntity" in str(e)):
          # Ignore if all ready detached
          pass
        else:
          # logging
          errorExceptionInfo = "[awsFinish | {}] Failed to detach User {} from Managed Local Policy: {} Error: {}".format(accountName, user, policyArn, str(e))
          logging.exception(errorExceptionInfo)
          # DBConnect ============================
          # Update task['errorInfo']
          DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
          # ======================================
          failFlag.append("Error: {}".format(errorExceptionInfo))

    # 2 Detach from all groups
    for group in listOfGroups:
      try:
        session.client("iam").detach_group_policy(GroupName = str(group), PolicyArn = str(policyArn))
        # logging
        logging.info("[awsFinish | {}] Detached Group: {} from Managed Local Policy: {}".format(accountName, group, policyArn))
      except Exception as e:
        if("NoSuchEntity" in str(e)):
          # Ignore if all ready detached
          pass
        else:
          # logging
          errorExceptionInfo = "[awsFinish | {}] Failed to detach Group {} from Managed Local Policy: {} Error: {}".format(accountName, group, policyArn, str(e))
          logging.exception(errorExceptionInfo)
          # DBConnect ============================
          # Update task['errorInfo']
          DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
          # ======================================
          failFlag.append("Error: {}".format(errorExceptionInfo))

    # 3 Detach from all roles
    for role in listOfRoles:
      if(role not in whiteListedRoles):
        try:
          session.client("iam").detach_role_policy(RoleName = role, PolicyArn = str(policyArn))
          # logging
          logging.info("[awsFinish | {}] Detached Role: {} from Managed Local Policy: {}".format(accountName, role, policyArn))
        except Exception as e:
          if("NoSuchEntity" in str(e)):
            # Ignore if all ready detached
            pass
          else:
            # logging
            errorExceptionInfo = "[awsFinish | {}] Failed to detach Role {} from Managed Local Policy: {} Error: {}".format(accountName, role, policyArn, str(e))
            logging.exception(errorExceptionInfo)
            # DBConnect ============================
            # Update task['errorInfo']
            DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
            # ======================================
            failFlag.append("Error: {}".format(errorExceptionInfo))

  # Delete all the managed policies
  for arn in listOfArns:
    try:
      session.client("iam").delete_policy(PolicyArn = str(arn))
      logging.info("[awsFinish | {}] Deleting Managed Policy: {} ".format(accountName, str(arn)))
    except Exception as e:
      if("NoSuchEntity" in str(e)):
        # Ignore if all ready deleted
        pass
      else:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete Managed Policy: '{}' Error:{}".format(accountName, str(arn), str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))


# ----------------------------------------
# Deleting All Dependencies From All Users
# ----------------------------------------
def deleteAllDependenciesFromAllUsers(session, listOfUsers, logging, accountName, taskId, failFlag):
  # user all ready does not belong to any groups(code above)
  # for each user:
  for user in listOfUsers:
    # Access Keys for the user
    listOfAccessKeys = []
    # Signing Certificates for the user
    listOfSigningCertificates = []
    # MFA devices for the user
    listOfMFADevices = []
    # User Inline Policies
    listOfUserInlinePolicies = []
    # Users Managed Policies
    listOfUserManagedPolicies = []

    # Raw data for users access keys
    accessKeys = session.client("iam").list_access_keys(UserName = user)

    # ------------------------------------
    # Getting all access keys for the user
    # ------------------------------------
    logging.info("[awsFinish | {}] Getting Access Keys...".format(accountName))
    for accessKey in accessKeys["AccessKeyMetadata"]:
      listOfAccessKeys.append(accessKey["AccessKeyId"])

    # -------------------------------------
    # Deleting all access keys for the user
    # -------------------------------------
    logging.info("[awsFinish | {}] Deleting Access Keys...".format(accountName))
    accessKeysToDelete = []
    for accessKeyId in listOfAccessKeys:
      try:
        session.client("iam").delete_access_key(UserName = user, AccessKeyId = accessKeyId)
        accessKeysToDelete.append(accessKeyId)
        # logging
        logging.info("[awsFinish | {}] Deleting Access Key: '{}'".format(accountName, accessKeyId))
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete Access Key: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
    # now remove all access keys from the main array
    for i in accessKeysToDelete:
      listOfAccessKeys.remove(i)


    # ----------------------------
    # Get all Signing Certificates
    # ----------------------------
    logging.info("[awsFinish | {}] Getting Signing Certificates...".format(accountName))
    groupSigningCertificates = session.client("iam").list_signing_certificates(UserName=user)

    for signingCert in groupSigningCertificates["Certificates"]:
      listOfSigningCertificates.append(signingCert["CertificateId"])

    # ----------------------------------------------
    # Deleting all signing Certificates for the user
    # ----------------------------------------------
    logging.info("[awsFinish | {}] Deleting Signing Certificates...".format(accountName))
    signingCertificatesToDelete = []
    for signingCertificateId in listOfSigningCertificates:
      try:
        session.client("iam").delete_signing_certificate(UserName = user, CertificateId = signingCertificateId)
        signingCertificatesToDelete.append(signingCertificateId)
        # logging
        logging.info("[awsFinish | {}] Deleting Signing Certificate: '{}'".format(accountName, signingCertificateId))
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete Signing Certificate: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
    # now remove all signing certificates from the main array
    for i in signingCertificatesToDelete:
      listOfSigningCertificates.remove(i)

    # -------------------
    # Get all MFA Devices
    # -------------------
    logging.info("[awsFinish | {}] Getting MFA Devices...".format(accountName))
    mfaDevices = session.client("iam").list_mfa_devices(UserName=user)

    for mfaDevice in mfaDevices["MFADevices"]:
      listOfMFADevices.append(mfaDevice["SerialNumber"])

    # -----------------------------------------
    # Deactivating all MFA Devices for the user
    # -----------------------------------------
    logging.info("[awsFinish | {}] Deactivating MFA Devices...".format(accountName))
    for mfaDeviceSerialNumber in listOfMFADevices:
      try:
        # Deactivating the MFA Device
        session.client("iam").deactivate_mfa_device(UserName = user,SerialNumber = mfaDeviceSerialNumber)
        # logging
        logging.info("[awsFinish | {}] Deactivating MFA Device: '{}'".format(accountName, mfaDeviceSerialNumber))
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to deactivate MFA Device: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))


    # -------------------------------------
    # Deleting all MFA Devices for the user
    # -------------------------------------
    ##print("\nDeleting MFA Devices", end=" ")
    logging.info("[awsFinish | {}] Deleting MFA Devices...".format(accountName))
    mfaDevicesToDelete = []
    for mfaDeviceSerialNumber in listOfMFADevices:
      try:
        # Deleting the MFA Device
        session.client("iam").delete_virtual_mfa_device(SerialNumber = mfaDeviceSerialNumber)
        mfaDevicesToDelete.append(mfaDeviceSerialNumber)
        # logging
        logging.info("[awsFinish | {}] Deleting MFA Device: '{}'".format(accountName, mfaDeviceSerialNumber))
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete MFA Device: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
    # now remove all MFA devices from the main array
    for i in mfaDevicesToDelete:
      listOfMFADevices.remove(i)

    # ---------------------------------------------
    # Deleting all the Inline Policies for the user
    # ---------------------------------------------
    userInlinePoliciesRaw = session.client("iam").list_user_policies(UserName = user)

    logging.info("[awsFinish | {}] Getting User Inline Policies...".format(accountName))
    for userInlinePolicy in userInlinePoliciesRaw["PolicyNames"]:
      listOfUserInlinePolicies.apppend(userInlinePolicy)
      # logging
      logging.info("[awsFinish | {}] getting inline policy: {}".format(accountName, userInlinePolicy))

    logging.info("[awsFinish | {}] Deleting User Inline Policies...".format(accountName))
    inlinePoliciesToDelete = []
    for userinlinePolicy in listOfUserInlinePolicies:
      try:
        session.client("iam").delete_user_policy(UserName = user, PolicyName = userinlinePolicy)
        # removing policy from listOfUserInlinePolicies
        inlinePoliciesToDelete.append(userinlinePolicy)
        # logging
        logging.info("[awsFinish | {}] Deleting User Inline Policy: '{}'".format(accountName, userinlinePolicy))
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete User Inline Policy: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
    # now remove all inline policies from the main array
    for i in inlinePoliciesToDelete:
      listOfUserInlinePolicies.remove(i)

    # -----------------------------------------------
    # Detaching all the Managed Policies for the user
    # -----------------------------------------------
    # These policies that are created by the user(Can be empty)
    userManagedPoliciesRaw = session.client("iam").list_attached_user_policies(UserName = user)

    logging.info("[awsFinish | {}] Getting User Managed Policies...".format(accountName))
    for userManagedPolicy in userManagedPoliciesRaw["AttachedPolicies"]:
      listOfUserManagedPolicies.append(userManagedPolicy["PolicyArn"])
      # logging
      logging.info("[awsFinish | {}] Deleting User Managed Policy: '{}'".format(accountName, userManagedPolicy))

    logging.info("[awsFinish | {}] Detaching User Managed Policies...".format(accountName))
    managedPoliciesToDelete = []
    for userManagedPolicyArn in listOfUserManagedPolicies:
      try:
        session.client("iam").detach_user_policy(UserName = user, PolicyArn = userManagedPolicyArn)
        # removing polict from listOfUserManagedPolicies
        managedPoliciesToDelete.append(userManagedPolicyArn)
        # logging
        logging.info("[awsFinish | {}] Deleting User Managed Policy: '{}'".format(accountName, userManagedPolicyArn))
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to detach User Managed Policy: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
    # now remove all managed policies from the main array
    for i in managedPoliciesToDelete:
      listOfUserManagedPolicies.remove(i)


# -----------------
# Deleting the User
# -----------------
def deleteAllUsers(session, listOfUsers, logging, accountName, taskId, failFlag):
  # Deleting the login profile for each user and then deleting the user
  for user in listOfUsers:
    try:
      session.client("iam").delete_login_profile(UserName = user)
    except Exception as e:
      if("NoSuchEntity" in str(e)):
        # Ignore as there is no login profile for this user
        # This can happen when the createAdmin breaks after creating an user but before assigning a login profile
        pass
      else:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete User Log-In Profile: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))

  # Deleting the user
  usersToDelete = []
  for user in listOfUsers:
    try:
      session.client("iam").delete_user(UserName = user)
      # removing user form listOfUsers
      usersToDelete.append(user)
      # logging
      logging.info("[awsFinish | {}] Deleting User: '{}'".format(accountName, user))
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to delete User: {}".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))
  # now remove all users from the main array
  for i in usersToDelete:
    listOfUsers.remove(i)


# -----------------------------
# Getting all EC2 Instances Ids
# -----------------------------
def getAllEc2Instances(session, listOfInstancesIds):
  # Getting all instances (Not terminated ones)
  ec2Instances = session.client("ec2").describe_instances()
  # Add all the instanes Id's into an array
  for instance in ec2Instances["Reservations"]:
    for instance2 in instance["Instances"]:
      # appending them to 'listOfInstancesIds'
      listOfInstancesIds.append(instance2["InstanceId"])


# -----------------------------------------------------
# Disabling Termination Protection in all EC2 Instances
# -----------------------------------------------------
def disableTerminationProtectionForAllEc2Instances(session, listOfInstancesIds, logging, accountName, taskId, failFlag):
  # Get raw information about instances
  instanceStatusRaw = session.client("ec2").describe_instance_status(InstanceIds = listOfInstancesIds)
  # For each instance, check if the Termination Protection is turned on, if so, disable it
  for instance in instanceStatusRaw["InstanceStatuses"]:
    try:
      if (session.client("ec2").describe_instance_attribute(InstanceId = instance["InstanceId"], Attribute = "disableApiTermination")):
        session.client("ec2").modify_instance_attribute(InstanceId = instance["InstanceId"], DisableApiTermination = {'Value': False})
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to disable Termination Protection: {}".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))


# -----------------------------
# Terminating all EC2 Instances
# -----------------------------
def terminateAllEc2Instances(session, listOfInstancesIds, logging, accountName, taskId, failFlag):
  # Terminating all instances
  try:
    session.client("ec2").terminate_instances(InstanceIds = listOfInstancesIds)
    # logging
    logging.info("[awsFinish | {}] Terminating Instances: '{}'".format(accountName, listOfInstancesIds))
  except Exception as e:
    # logging
    errorExceptionInfo = "[awsFinish | {}] Failed to terminate instances: {}".format(accountName, str(e))
    logging.exception(errorExceptionInfo)
    # DBConnect ============================
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
    # ======================================
    failFlag.append("Error: {}".format(errorExceptionInfo))

# ---------------------
# Getting all Key-Pairs
# ---------------------
def getAllKeyPairs(session, listOfKeyPairs):
  # describing all key pairs
  keyPairs = session.client("ec2").describe_key_pairs()
  # Getting all the Key Pairs from keyPairsRaw into listOfKeyPairs array
  for keyPair in keyPairs["KeyPairs"]:
    listOfKeyPairs.append(keyPair["KeyName"])

# ----------------------
# Deleting all Key-Pairs
# ----------------------
def deleteAllKeyPairs(session, listOfKeyPairs, logging, accountName, taskId, failFlag):
  # Deleting all Key Pairs in the listOfKeyPairs array
  # DO NOT REMOVE FROM LIST AS LOOPING THROUGH IT... (Will skip some keys) have a second loop at the end
  listOfKeyPairsToDeleteAfterTheForLoop = []
  for keyPairName in listOfKeyPairs:
    logging.info("[awsFinish | {}] List of Key-Pair's: '{}'".format(accountName, listOfKeyPairs))
    try:
      session.client("ec2").delete_key_pair(KeyName = keyPairName)
      listOfKeyPairsToDeleteAfterTheForLoop.append(keyPairName)
      # logging
      logging.info("[awsFinish | {}] Deleting Key-Pair: '{}'".format(accountName, keyPairName))
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to delete Key-Pair: {}".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))
  # Only now remove the key-pairs
  for keyToRemove in listOfKeyPairsToDeleteAfterTheForLoop:
    listOfKeyPairs.remove(keyToRemove)

# -------------------
# Getting all Buckets
# -------------------
def getAllBuckets(session, listOfBuckets):
  # BEFORE DELETING A BUCKET: All objects (including all object versions and Delete Markers) in the bucket must be deleted before the bucket itself can be deleted
  # https://stackoverflow.com/questions/43326493/what-is-the-fastest-way-to-empty-s3-bucket-using-boto3
  buckets = session.client("s3").list_buckets()
  # Getting all buckets
  for bucket in buckets["Buckets"]:
    listOfBuckets.append(bucket["Name"])


# --------------------
# Deleting all Buckets
# --------------------
def deletingAllBuckets(session, s3ForDeletingBucket, listOfBuckets, logging, accountName, taskId, failFlag):
  # Need to delete many tmes in case if a bucket fails to delete. Did not find force delete in boto3
  counter = 0
  while(counter <= 4):
    # check if the listOfBuckets is empty, if so, break out of the loop
    if(not listOfBuckets):
      break
    # Emptying all buckets form listOfBuckets and deleting them
    listOfBucketsToDeleteFromMainList = []
    for bucket in listOfBuckets:
      try:
        theBucket = s3ForDeletingBucket.Bucket(bucket)
        # emptying the bucket
        theBucket.objects.all().delete()
        time.sleep(10)
        # Deleting the bucket
        session.client("s3").delete_bucket(Bucket = bucket)
        # Remove the bucket from listOfBuckets
        listOfBucketsToDeleteFromMainList.append(bucket)
        # logging
        logging.info("[awsFinish | {}] Deleting Bucket: '{}'".format(accountName, bucket))
      except Exception as e:
        if("The specified bucket does not exist" in str(e)):
          # logging
          logging.warning("[awsFinish | {}] {}".format(accountName, str(e)))
        else:
          ### Will ingore the failed to delete bucket error because of the while loop and counter ###
          logging.warning("[awsFinish | {}] {}".format(accountName, str(e)))
    # now remove all buckets from the main array
    for i in listOfBucketsToDeleteFromMainList:
      listOfBuckets.remove(i)
    # logging
    logging.info("[awsFinish | {}] Deleting buckets, loop: {}/4...".format(accountName, str(counter)))
    # Add counter
    counter = counter + 1
    # sleep for 10 sec
    time.sleep(10)


# ----------------------------------
# Getting all Cloud Formation Stacks
# ----------------------------------
def getAllCloudFormationStacks(session, listOfCloudFormationStacks):
  # describing all stacks
  cloudFormationStacks = session.client("cloudformation").describe_stacks()
  # for each cloud formation stack, get its name and append it to an array
  for cloudStack in cloudFormationStacks["Stacks"]:
    listOfCloudFormationStacks.append(cloudStack["StackName"])


# -----------------------------------
# Deleting all Cloud Formation Stacks
# -----------------------------------
def deleteAllCloudFormationStacks(session, listOfCloudFormationStacks, logging, accountName, taskId, failFlag):
  while(listOfCloudFormationStacks):
    # for each item in the array
    listOfCloudFormationStacksToDelete = []
    for cloudStack in listOfCloudFormationStacks:
      try:
        # Delete the stack
        session.client("cloudformation").delete_stack(StackName = cloudStack)
        # logging
        logging.info("[awsFinish | {}] Deleting Cloud Formation Stack:{}".format(accountName, cloudStack))
        # Remove from the listOfCloudFormationStacks
        listOfCloudFormationStacksToDelete.append(cloudStack)
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete Cloud Formation Stack: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
    # now remove all cloudFormation stacks from the main array
    for i in listOfCloudFormationStacksToDelete:
      listOfCloudFormationStacks.remove(i)


# ------------------------
# Getting all Cloud Trails
# ------------------------
def getAllCloudTrails(session, listOfCloudTrails):
  cloudTrails = session.client("cloudtrail").describe_trails()
  # Getting all the Cloud Trail Names into an array
  for cloudTrail in cloudTrails["trailList"]:
    listOfCloudTrails.append(cloudTrail["Name"])

# -------------------------
# Deleting all Cloud Trails
# -------------------------
def deleteAllCloudTrails(session, listOfCloudTrails, logging, accountName, taskId, failFlag):
  # Deleting all the Cloud Trails from listOfCloudTrails array
  cloudTrailsToDelete = []
  for cloudTrailName in listOfCloudTrails:
    try:
      session.client("cloudtrail").delete_trail(Name = cloudTrailName)
      # Remove from array
      cloudTrailsToDelete.append(cloudTrailName)
      # logging
      logging.info("[awsFinish | {}] Deleting Cloud Trail: '{}'".format(accountName, cloudTrailName))
    except Exception as e:
      if("TrailNotFoundException" in str(e)):
        pass
      else:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete Cloud Trail: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
  # now remove all cloud trails from the main array
  for i in cloudTrailsToDelete:
    listOfCloudTrails.remove(i)


# ---------------------
# Getting all Flow Logs
# ---------------------
def getAllFlowLogs(session, listOfFlowLogIds):
  flowLogs = session.client("ec2").describe_flow_logs()
  try:
    # Getting all the Flow Logs Names into an array
    for flowLog in flowLogs["FlowLogs"]:
      # The "FlowLogId" can be null, error returned, thats why try - except
      listOfFlowLogIds.append(flowLog["FlowLogId"])
  except Exception as e:
    # logging
    logging.warning("No Flow Logs Found: {}".format(str(e)))

# ----------------------
# Deleting all Flow Logs
# ----------------------
def deleteAllFlowLogs(session, listOfFlowLogIds, logging, accountName, taskId, failFlag):
  logging.info("[awsFinish | {}] Deleting All Flow Logs...".format(accountName))
  try:
    session.client("ec2").delete_flow_logs(FlowLogIds = listOfFlowLogIds)
    # logging
    logging.info("[awsFinish | {}] Deleting Flow Logs: '{}'".format(accountName, listOfFlowLogIds))
  except Exception as e:
    if("InvalidFlowLogId.NotFound" in str(e)):
      pass
    else:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to delete Flow Logs: {}".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))


# ----------------------------------
# Getting all Cloud Watch Log Groups
# ----------------------------------
def getAllCloudWatchLogGroups(session, listOfCloudWatchLogGroups):
  cloudWatchLogGroupsRaw = session.client("logs").describe_log_groups()
  for logGroup in cloudWatchLogGroupsRaw["logGroups"]:
    listOfCloudWatchLogGroups.append(logGroup["logGroupName"])

# -----------------------------------
# Deleting All Cloud Watch Log Groups
# -----------------------------------
def deleteAllCloudWatchLogGroups(session, listOfCloudWatchLogGroups, logging, accountName, taskId, failFlag):
  cloudWatchLogGroupsToDelete = []
  for logGroupName in listOfCloudWatchLogGroups:
    try:
      session.client("logs").delete_log_group(logGroupName = logGroupName)
      cloudWatchLogGroupsToDelete.append(logGroupName)
      # logging
      logging.info("[awsFinish | {}] Deleting Cloud Watch Log Group: '{}'".format(accountName, logGroupName))
    except Exception as e:
      if("ResourceNotFoundException" in str(e)):
        pass
      else:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to delete Cloud Watch Log Group: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
  # now remove all cloudWatch log groups from the main array
  for i in cloudWatchLogGroupsToDelete:
    listOfCloudWatchLogGroups.remove(i)


# ----------------------------
# Deleting all Security Groups
# ----------------------------
def deleteAllSecurityGroups(session, logging, accountName):
  # This function will be attempted 10 times(max 10 min) waiting for all instances to terminate
  listOfRuns = [1,2,3,4,5,6,7,8,9,10]
  # finish flag to exit the function
  finishFlag = 0
  # Deleting all Security Groups
  # While there is still some Security Group to delete
  for run in listOfRuns:
    # logging
    logging.info("[awsFinish | {}] Deleteing All Security Groups, Run: {}".format(accountName, run))

    # List of all Security Groups extracted from securityGroupsRaw
    listOfSecurityGroupIds = []

    # if the function has been attempted 10 times, exit with timeout
    if(run == 10):
      # set the timeout
      finishFlag = 2

    if(finishFlag == 1):
      # logging
      logging.info("[awsFinish | {}] Deleted all Security Groups...".format(accountName))
      break

    if(finishFlag == 2):
      # logging
      logging.warning("[awsFinish | {}] Failed to Delete all Security Groups...".format(accountName))
      break

    # The default security group cannot be deleted

    # Raw data for Role Security Groups
    securityGroupsRaw = session.client("ec2").describe_security_groups()

    # Getting Group Name and Group Id for each Security Group
    logging.info("[awsFinish | {}] Getting information about Security Groups...".format(accountName))
    for secGroup in securityGroupsRaw["SecurityGroups"]:
      # Skipping the default security group and appending all others to arrays
      if(not(secGroup["GroupName"] == "default")):
        listOfSecurityGroupIds.append(secGroup["GroupId"])

    # Do only if there is something in the array
    if(not listOfSecurityGroupIds):
      finishFlag = 1
      break

    # timeout variable to break ot of loop
    innerTimeout = 0
    # exit flag
    innerExitFlag = 0
    logging.info("[awsFinish | {}] Waiting for all Instances to Terminate...".format(accountName))
    # Exit after 60 seconds
    while(innerExitFlag == 0):
      # Trying to Delete each Security Group. Some groups relay on others which is why there is an array for leftover groups
      # Leftover groups are deleted after in a second for loop below
      securityGroupsToDelete = []
      for secGroup in listOfSecurityGroupIds:
        try:
          session.client("ec2").delete_security_group(GroupId = secGroup)
          securityGroupsToDelete.append(secGroup)
          # logging
          logging.info("[awsFinish | {}] Deleting Security Group: '{}'".format(accountName, secGroup))
        except:
          # waiting for instances to terminate
          logging.info("[awsFinish | {}] Waiting for all Instance to Terminate...".format(accountName))
      # now remove all security groups from the main array
      for i in securityGroupsToDelete:
        listOfSecurityGroupIds.remove(i)
      # When array is empty(All Security Groups deleted excpt the default), exit the while loop
      if(not listOfSecurityGroupIds):
        # All security groups deleted
        innerExitFlag = 1
        finishFlag = 1
      # Error/Timeout break out of loop
      if(innerTimeout >= 6):
        innerExitFlag = 1
      # timeout variable incremented
      innerTimeout = innerTimeout + 1
      # Sleep timer for the while loop
      time.sleep(10)

# ------------------
# Deleting all Roles
# ------------------
def deleteAllRoles(session, listOfRoles, whiteListedRoles, logging, accountName, taskId, failFlag):
  # Try-Except: function throws exceptions, but deletes the roles...
  # list of roles to work with and delete
  rolesToDelete = []
  rolesToDeleteAtTheEndOfForLoopNotInIt = []

  # if a role is not on the white list, append it to "rolesToDelete"
  for role in listOfRoles:
    if (role not in whiteListedRoles):
      rolesToDelete.append(role)
  # Getting raw data about all Role Inline Policies for each role
  for role in rolesToDelete:
    # list of role instance profiles
    listOfCurrentRoleInstanceProfiles = []
    # getting instance profiles
    logging.info("[awsFinish | {}] Getting Role Instance Profiles...".format(accountName))

    # throws exception
    try:
      # Raw data for Role Instance Profiles
      instanceProfilesRaw = session.client("iam").list_instance_profiles_for_role(RoleName = role)
      # get a list of instance profiles for the role
      for instance in instanceProfilesRaw["InstanceProfiles"]:
        listOfCurrentRoleInstanceProfiles.append(instance["InstanceProfileName"])
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to get Instance Profile: {}".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))

    # deleting these instance profiles
    logging.info("[awsFinish | {}] Deleting Role Instance Profiles...".format(accountName))
    # throws exception
    try:
      roleInstanceProfilesToDelete = []
      # delete all the instance profiles for the role
      for instanceProfile in listOfCurrentRoleInstanceProfiles:
        # remove_role_from_instance_profile
        session.client("iam").remove_role_from_instance_profile(InstanceProfileName = instanceProfile, RoleName = role)
        # removing the instance profile from the list
        roleInstanceProfilesToDelete.append(instanceProfile)
        # logging
        logging.info("[awsFinish | {}] Deleting Instance Profile: '{}'".format(accountName, instanceProfile))
      # now remove all cloudWatch log groups from the main array
      for i in roleInstanceProfilesToDelete:
        listOfCurrentRoleInstanceProfiles.remove(i)
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to delete Instance Profile.".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))

    # deleting role inline policies
    logging.info("[awsFinish | {}] Deleting Role Inline Policies...".format(accountName))
    # throws exception
    try:
      # Raw data for Role Inline Policies
      roleInlinePoliciesRaw = session.client("iam").list_role_policies(RoleName = role)

      # for each Role Inline Policy, Delete it
      for inlinePolicy in roleInlinePoliciesRaw["PolicyNames"]:
        # delete_role_policy
        session.client("iam").delete_role_policy(RoleName = role, PolicyName = inlinePolicy)
        # logging
        logging.info("[awsFinish | {}] Deleting Role Inline Policy: '{}'".format(accountName, inlinePolicy))
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to delete Role Inline policy: {}".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))

    # detachig role managed policies
    logging.info("[awsFinish | {}] Detaching Role Managed Policies...".format(accountName))
    # throws exception
    try:
      # Raw data for Role Managed Policies
      roleManagedPoliciesRaw = session.client("iam").list_attached_role_policies(RoleName = role)
      # for each Role Managed Policy,
      for managedPolicy in roleManagedPoliciesRaw["AttachedPolicies"]:
        # detach_role_policy
        session.client("iam").detach_role_policy(RoleName = role, PolicyArn = managedPolicy["PolicyArn"])
        # logging
        logging.info("[awsFinish | {}] Detaching Role Managed Policy: '{}'".format(accountName, managedPolicy["PolicyArn"]))
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to delete Role Managed Policy: {}".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))

    # finally deleting the role
    logging.info("[awsFinish | {}] Deleting Roles...".format(accountName))
    # throws exception
    try:
      # deleting the role after removing all inline policies and detaching all managed policies
      session.client("iam").delete_role(RoleName = role)
      if role in listOfRoles: listOfRoles.remove(role)
      # logging
      logging.info("[awsFinish | {}] Deleting Role: '{}'".format(accountName, role))
    except Exception as e:
      # logging
      errorExceptionInfo = "[awsFinish | {}] Failed to delete Role: {}".format(accountName, str(e))
      logging.exception(errorExceptionInfo)
      # DBConnect ============================
      # Update task['errorInfo']
      DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
      # ======================================
      failFlag.append("Error: {}".format(errorExceptionInfo))

  # finish roles deleted
  logging.info("[awsFinish | {}] Roles Deleted.".format(accountName))

# -------------------------
# Deleting all Elastic IP's
# -------------------------
def findAndDeleteAllElasticIPs(session, taskId, failFlag, accountName, logging):
  # Get all the Elastic IP's.
  # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_addresses
  elasticIps = session.client("ec2").describe_addresses()
  # For each elastic ip: disassociate_address if it is associated and always release_address
  for elasticIp in elasticIps['Addresses']:
    if("AssociationId" in elasticIp):
      # ===================================================================================================================
      # 1 Disassociating the Elastic IP's if is is associated
      # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.disassociate_address
      # ===================================================================================================================
      try:
        # ------------------------
        # Disassociate the address
        # ------------------------
        session.client("ec2").disassociate_address(AssociationId=str(elasticIp['AssociationId']))
      except Exception as e:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to disassociate ElasticIP address: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
    # ==============================================================================================================
    # 2 Releasing the Elastic IP's (will always have AllocationId)
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.release_address
    # ==============================================================================================================
    try:
      # -------------------
      # Release the address
      # -------------------
      session.client("ec2").release_address(AllocationId=str(elasticIp['AllocationId']))
    except Exception as e:
      # Ignore the 'AuthFailure' error as it means that the IP is already allocated to another AWS account.
      if("AuthFailure" in str(e)):
        pass
      else:
        # logging
        errorExceptionInfo = "[awsFinish | {}] Failed to release ElasticIP: {}".format(accountName, str(e))
        logging.exception(errorExceptionInfo)
        # DBConnect ============================
        # Update task['errorInfo']
        DBConnect.appendTaskErrorInfo(taskId, accountName, errorExceptionInfo)
        # ======================================
        failFlag.append("Error: {}".format(errorExceptionInfo))
    logging.info("[awsFinish | {}] Released Elastic IP...".format(accountName))

