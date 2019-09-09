import sys, pymongo, logging
from bson import ObjectId

def main(request):
  
  # path for output file ===============
  sys.path.append("../boru/licenseInfo")
  # ====================================

  # logging ============================================================================================================
  logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
  log = logging.getLogger('license')
  log.info("[createLicence] Working...")
  # ====================================

  # info for output file ===================
  keys = request['parameters'][0][0]['keys']
  tag = request['tag']
  startDate = request['startDate'].replace(" ", "-")
  # ================================================

  # writing to file =================================================================
  f = open("../licenseInfo/{}-{}-licenses.txt".format(str(tag), str(startDate)), "a")
  print("Here are the licenses for: {}-{}\nKeys-> {}".format(str(tag), str(startDate), str(keys)), file = f)
  # Don't forget!
  f.close()
  # =======

  # changing task status ============
  mongoClient = pymongo.MongoClient()
  mongodb = mongoClient.boruDB

  taskIdStr = request['task_id']
  task_id = ObjectId(taskIdStr)

  mongodb.tasks.update_one({ "_id": task_id }, { "$set": { "taskStatus": "ready" } })
  mongoClient.close()
  # =================

