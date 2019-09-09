import pymongo, logging
from bson import ObjectId
def main(request):
  # test logging
  logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
  log = logging.getLogger('license')
  log.info("[dummyScript] Working nothing...")

  mongoClient = pymongo.MongoClient()
  mongodb = mongoClient.boruDB

  taskIdStr = request['task_id']
  task_id = ObjectId(taskIdStr)

  mongodb.tasks.update_one({ "_id": task_id }, { "$set": { "taskStatus": "ready" } })
  mongoClient.close()
