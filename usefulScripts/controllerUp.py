import sys, pymongo, datetime, requests

def main():
  # List of URL's
  listOfLinks = []
  # ===========================================================================
  # Read the txt file and append the contents to the list of URL's line by line
  # ===========================================================================
  # open file
  f = open("/var/log/controllers.log", "r")
  for i in f:
    listOfLinks.append(i.rstrip())
  # file close
  f.close()
  # ========================================================================================
  # Call each link and wait for a response. If there is no startDate in the database,
  # use the current date (UTC) as startDate. If there is a startDate, update the finishDate.
  # If there is no response, don't update anything.
  # ========================================================================================
  # MongoDB connection
  mongoClient = pymongo.MongoClient()
  mongodb = mongoClient.controllerDB
  s = requests.Session()
  # For each controller link
  for controllerLink in listOfLinks:
    # currentDate
    currentTime = datetime.datetime.utcnow()
    # API call
    # try, except returns 'Name or service not known' (not up)
    try:
      apiResponse = s.get(str(controllerLink))
      # Update the database
      # Check it document is in the database
      document = mongodb.controllers.find({"link" : str(controllerLink)})
      # if there is no document with that link, create the document
      if(document.count() == 0):
        mongodb.controllers.insert({"link" : str(controllerLink), "startDate" : currentTime, "finishDate" : currentTime})
      # Else, update the finishDate of the document
      elif(apiResponse.status_code == 200):
        mongodb.controllers.update({"link" : str(controllerLink)}, { "$set" : {"finishDate" : currentTime}})
      else:
        # Not up
        pass
    except:
      # Not up
      pass
  # MongoDB close
  mongoClient.close()
  # Session close
  s.close()
  # ==============================================
  # MongoDB Structure - db.controllers Collection
  # {
  #   _id : ObjectId("1a1111a1a2aa22222b2222b2")
  #   link : https://something.com
  #   startDate : ISODate("2019-07-01T07:00:00Z")
  #   finishDate : ISODate("2019-07-01T10:49:00Z")
  # }
  # ==============================================

main()