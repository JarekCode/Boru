# ------------------
# John Ó Ríordán
# ------------------
# ---------------------------------------------------
# plugin_userPassword.py |  Return a password
# In the futrue this will take 2 inputs
# RANDOM < Special Keyword to tell it to generate a random password
# String < This string is the password
# --------------------------------------------------
#### Fri Apr 12 11:44:24 IST 2019
##   Updated by Jarek to fix an error - "userPasword" should be "userPassword".

import boto3, json

# This is the default function name and variables. Every script has to have this function and variable names. 
def getIdentifier(labName, region, identifier):
    return json.dumps({'userPassword' : 'Password1!'})

    # The function should return a json key pair with either "identfierr : result" or "error : error_string".
    # Identifier should match the paremeter expected by the cloudFormation Template
    # Result is the value passed to that paramter


