#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# The scripts only runs when there are no: starting, finishing, suspending, resuming jobs in scheduledJobs collection and there are no tasks in tasks collection.
import pymongo, time, logging, sys, subprocess

# DEBUG MODE (to debug crontab)
debugFlag = True

# location of restartBoru script
sys.path.append("/usr/local/bin")

# MongoDB
mongoClient = pymongo.MongoClient()
mongodb = mongoClient.boruDB

# Logging
logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
log = logging.getLogger('boruWeeklyRestart')

# Timeout variable
timeoutVariable = 600

# Timeout counter
timeoutCounter = 0
timeoutCounterLimit = 10

# DEBUG MODE ONLY
if(debugFlag):
  log.warning("[Restart DEBUG] Starting restart script....")

# Keep trying until timout or success
while True:
  # Read all scheduledJobs
  allScheduledJobs = mongodb.scheduledJobs.find()

  # DEBUG MODE ONLY
  if(debugFlag):
    log.warning("[Restart DEBUG] Got All Scheduled Jobs.")

  # Look at every job
  for job in allScheduledJobs:
    
    # DEBUG MODE ONLY
    if(debugFlag):
      log.warning("[Restart DEBUG] For Loop Job...")
    
    # If a job is: starting, finishing, suspending or resuming
    if(job['jobStatus'] == "starting" or job['jobStatus'] == "finishing" or job['jobStatus'] == "suspending" or job['jobStatus'] == "resuming"):
      # Log
      log.warning("[Restart] Waiting {} seconds before attempting restart again. Some jobs in progress.".format(str(timeoutVariable)))
      # increase counter
      timeoutCounter = timeoutCounter + 1
      # Wait for "timeoutVariable" and try again
      time.sleep(timeoutVariable)

  # Next see if there are any tasks in the tasks collection

  # Read all tasks
  allTasks = mongodb.tasks.find()

  # DEBUG MODE ONLY
  if(debugFlag):
    log.warning("[Restart DEBUG] Got All Tasks.")

  # Go and restart Boru
  if(allTasks.count() == 0):

    # DEBUG MODE ONLY
    if(debugFlag):
      log.warning("[Restart DEBUG] About to restart Boru.")

    # Restart Boru [ !!! Needs to be full path for crontab to work ]
    subprocess.call("/usr/local/bin/restartBoru")
    # Log
    log.warning("[Restart] Boru has been restarted to release memory.")
    # End
    mongoClient.close()
    logging.shutdown()
    sys.exit()
  else:
    # Log
    log.warning("[Restart] Waiting {} seconds before attempting restart again. Some task in progress.".format(str(timeoutVariable)))
    # increase counter
    timeoutCounter = timeoutCounter + 1
    # Wait for "timeoutVariable" and try again
    time.sleep(timeoutVariable)

  if(timeoutCounter >= timeoutCounterLimit):
    # Log
    log.warning("[Restart] Failed to restart Boru after {} attempts.".format(str(timeoutCounter)))
    # End
    mongoClient.close()
    logging.shutdown()
    sys.exit()