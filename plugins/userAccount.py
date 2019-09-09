# ------------------
# John Ó Ríordán
# ------------------
# ---------------------------------------------------
# plugin_userAccount.py |  Return a username
# --------------------------------------------------

import boto3, json

# This is the default function name and variables. Every script has to have this function and variable names. 
def getIdentifier(labName, region, identifier):
    return json.dumps({'account' : str(labName)})

    # The function should return a json key pair with either "identfierr : result" or "error : error_string".
    # Identifier should match the paremeter expected by the cloudFormation Template
    # Result is the value passed to that paramter


