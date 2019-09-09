import boto3, json, sys

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_key_pair
def getIdentifier(labName, region, identifier):
  try:
    # Session | Used to access student child accounts
    session = boto3.Session(profile_name=labName, region_name=region)
    # Connect to EC2
    ec2Resources = session.client('ec2')

    # Create the Key-Pair with the name 'Sensor'
    response = ec2Resources.create_key_pair(KeyName = 'Sensor')

    # Get the Name of the Key-Pair from response
    keyPairName = response['KeyName']

    # Get the KeyMaterial
    keyMaterial = response['KeyMaterial']

    # path for output file =================
    sys.path.append("/var/www/html/sshkeys")
    # ======================================

    # writing to file ================================================
    f = open("/var/www/html/sshkeys/{}.pem".format(str(labName)), "w")
    print(str(keyMaterial), file = f)
    # Don't forget!
    f.close()
    # =======

    # Return Key-Pair Name
    return json.dumps({"KeyName" : str(keyPairName)})
  except Exception as e:
    return json.dumps({"error" : str(e)})
