#!/usr/bin/python3
# -*- coding: utf-8 -*-

# -------------------------------------------
# Name: YOUR NAME
# Version: 0.1
# Notes: ADD UPDATES HERE
# -------------------------------------------

# Imports
import json

# ---------------------------------------
# getIdentifier - Called by the scheduler
# ---------------------------------------
# labName - task['lab'] - Eg. 'Student01'
# region - task['region'] - Eg. 'us-east-1'
# identifier - db.courses collection - cloudFormationParameters[index]{'paramValue': 'THIS_VALUE'}
def getIdentifier(labName, region, identifier):

  try:
    # --------------
    # YOUR CODE HERE
    # --------------

    # SUCCESSFULL RETURN
    yourProcessedValue = "VALUE"
    return json.dumps({'KEY' : str(yourProcessedValue)})

  except Exception as e:
    # ERROR RETURN
    # NOTE: 'error' is a key reserved for failed processing of the plugin.
    return json.dumps({'error' : str(e)})
