import json

def getIdentifier(labName, region, identifier):
  # Return ApiProtection with value 'false'
  return json.dumps({"APITermination" : "false"})

