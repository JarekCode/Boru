# ------------------
# John Ó Ríordán
# ------------------
# ---------------------------------------------------
# plugin_delta.py |  Test plugin that returns the string that it was passed
# --------------------------------------------------

import boto3, json

# This is the default function name and variables. Every script has to have this function and variable names. 
def getIdentifier(labName, region, identifier):

    return json.dumps({'delta' : str(identifier)})

    # The function should return a json key pair with either "parameter_name : result" or "error : error_string"


