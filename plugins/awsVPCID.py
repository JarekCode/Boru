# ------------------
# John Ó Ríordán
# ------------------
# ---------------------------------------------------
# awsVPCID.py |  Get VPC ID for specified VPC Name
# --------------------------------------------------

import boto3, json

# This is the default function name and variables. Every script has to have this function and variable names. 
def getIdentifier(labName, region, identifier):
    try:
        # Session | Used to access student child accounts
        session = boto3.Session(profile_name=labName, region_name=region)
        # Connect to EC2
        ec2Resources = session.resource('ec2')
        # Creating a filter to return the vpc 
        filters = [{'Name':'tag:Name', 'Values':[identifier]}]

        # The vpcs, only one in our case is stored in a list called vpcs 
        vpcs = list(ec2Resources.vpcs.filter(Filters=filters))

        try: 
            # To extract the vpc_id, use method .vpc_id | Use dir(vpcs[0]) for a list of all functions.
            # We return only one item, therefore only index[0] is read
            trainingVPC = vpcs[0].vpc_id
        except Exception as e:
            return json.dumps({'error' : 'Unable to locate TrainingVPC'})

    except Exception as e:
        return json.dumps({'error' : str(e)})

    return json.dumps({'awsVPCID' : str(trainingVPC)})

    # The function should return a json key pair with either "identfierr : result" or "error : error_string"


