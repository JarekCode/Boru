import json

def getIdentifier(labName, region, identifier):
  # Return awsHTTPLocation named '0.0.0.0/0'
  return json.dumps({"HTTPLocation" : "0.0.0.0/0"})
