#!/usr/bin/python3
# -*- coding: utf-8 -*-

# -------------------------------------------
# Name: YOUR NAME
# Version: 0.1
# Notes: ADD UPDATES HERE
# -------------------------------------------

# Imports
import sys, logging

# Path to DBConnect
sys.path.append("../")
# Import DBConnect
import DBConnect

# Path to /opt/boru/plugins
sys.path.append("../boru/plugins")
# Import all plugins.
# You may be required to process plugins to start/finish/suspend/resume a lab.
from plugins import *

# ------------------------------
# main - Called by the scheduler
# ------------------------------
# jsonDoc - Everything passed in from the 'generateStartLabTaskBuffer'(or Finish or Suspend or Resume) function in the scheduler.
def main(jsonDoc):

  # ------------
  # Logger setup
  # ------------
  try:
    logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
    log = logging.getLogger('SCRIPT_NAME')
  except Exception as e:
    # No logging, just print, can't log :(
    print("[SCRIPT_NAME] Critical Logger Setup Error: {}".format(str(e)))
    # Exit
    return

  # -----------------------------------
  # Extracting the task_id from jsonDoc
  # -----------------------------------
  # Required to use DBConnect, passed into every jsonDoc.
  taskId = jsonDoc['task_id']

  # --------------
  # YOUR CODE HERE
  # --------------


  # --------------------------------------------------------------------------------------------------------------------
  # EXAMPLES BELOW
  # --------------------------------------------------------------------------------------------------------------------

  # ----------------------------------------------------------
  # Example of appending 'ERROR' information using 'DBConnect'
  # ----------------------------------------------------------
  # NOTE: This script MUST update the Task Status to 'Error' or 'Ready' before exiting any script.
  try:
    i = 10 / 0
  except Exception as e:
    # Logging
    errorExceptionInfo = "[SCRIPT_NAME] Example Function Error: {}".format(str(e))
    log.exception(errorExceptionInfo)
    # Update task['errorInfo']
    DBConnect.appendTaskErrorInfo(taskId, accountName, "Error: {}".format(str(e)))
    # Update task['taskStatus'] to 'Error'
    DBConnect.setTaskStatusToError(taskId)
    # Exit
    return

  # ------------------------------------------------------------
  # Example of appending 'SUCCESS' information using 'DBConnect'
  # ------------------------------------------------------------
  # NOTE: This script MUST update the Task Status to 'Ready' or 'Error' before exiting any script.
  # Update task['successInfo']
  DBConnect.appendTaskSuccessInfo(taskId, accountName, "Successful Info Here")
  # Update task['taskStatus'] to 'Ready'
  DBConnect.setTaskStatusToReady(taskId)
  # Exit
  return

  # --------------------------------------------------------------------------------------------------------------------