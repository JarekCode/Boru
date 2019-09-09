import boto3, json

def getIdentifier(labName, region, identifier):
  try:
    # Session | Used to access student child accounts
    session = boto3.Session(profile_name=labName, region_name=region)
    # Connect to EC2
    ec2Resources = session.client('ec2')

    # Get all subnets
    response = ec2Resources.describe_subnets()
    # Get subnetID
    for item in response['Subnets']:
      subnetID = item['SubnetId']
      # Return subnetID
      return json.dumps({"SubnetId" : str(subnetID)})
  except Exception as e:
    return json.dumps({"error" : str(e)})

