#!/usr/bin/python3
# -*- coding: utf-8 -*-

# ------------------
# Jaroslaw Glodowski
# ------------------

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# /root/.aws/config is being used for accounts
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#configuration
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ----------------------------------------
# version: 0.1.4 - Updated comments and presentation of code - 21/08/2019
# Boru.py - custom boru scheduler _/_\/_\_
# ----------------------------------------

import time, pymongo, datetime, logging, threading, json, ast, sys
from datetime import timedelta
from importlib import import_module
from systemd.journal import JournalHandler
from bson import ObjectId
# import plugins located in /plugins
from plugins import *
# import scripts located in /scripts
from scripts import *
# import scripts located in /notificationPlugins
from notificationPlugins import *
# config.py
sys.path.insert(0, '/etc/boru/')
import config

# ------------
# logger setup
# ------------
logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
# Logger named 'boru'
log = logging.getLogger('boru')
# Adding JournalHandler to the logger
log.addHandler(JournalHandler())

# Main function of the scheduler
def main():
  # logging, logged after every restart or startup
  log.warning("[Scheduler] -----------------------------------------------------------------------------")
  log.warning("[Scheduler] Starting Boru...")
  log.warning("[Scheduler] logging to /var/log/boru.log and journalctl")
  log.warning("[Scheduler] if this service keeps failing to start, run /opt/boru/boru for extra logging.")
  log.warning("[Scheduler] -----------------------------------------------------------------------------")

  # ----------------
  # mongo connection
  # ----------------
  try:
    # 1. setting up the mongo client
    # 2. specifying the mongo database = 'boruDB'
    mongoClient = pymongo.MongoClient()
    mongodb = mongoClient.boruDB
  except Exception as e:
    # logging
    log.exception("[Scheduler] Failed to establish connection with MongoDB: {}".format(str(e)))

  # -----------------------------
  # Getting values from config.py
  # -----------------------------
  try:
    # hours - task timeout if task is older then X hours - mark task as error
    taskTimeoutAfterCreation = config.getConfig("taskTimeoutAfterCreation")
    # hours - timeout if job is finishing for X hours - mark job as failedToFinish
    failedToFinishJobTimeout = config.getConfig("failedToFinishJobTimeout")
  except Exception as e:
    log.error("[Scheduler] Failed to read config.py Error: {}".format(str(e)))

  # ------------
  # cycleCounter
  # ------------
  # used to switch between two main parts of the scheduler, 1st tasks loop and 2nd jobs loop below
  cycleCounter = 2

  # main loop of the scheduler
  while(True):

    # Note: if you are reading code for the first time, start with the 'jobs' loop below tasks because a job creates tasks
    # ================================================
    #  _____         _        
    # |_   _|_ _ ___| | _____ 
    #   | |/ _` / __| |/ / __| 
    #   | | (_| \__ \   <\__ \ 
    #   |_|\__,_|___/_|\_\___/ 
    # ================================================
    # TASKS
    # =====

    # tasks are used whenever a job is being run. each task corresponds to only one action such as start one lab.
    # each job generates one or multiple tasks based on the action a job is performing such as start or finish lab and the number of labs specified.
    if(cycleCounter < 2):
      # getting all up to date tasks form db.tasks collection
      allTasks = getTasks(mongodb, log)

      # looping through every task, checking for different types and status combination.
      # each combination determines what part of the elif statement is accessed for that task.
      # note: task['taskStatus'] must be changed in the external scripts(awsStart.py) to ready/error
      for task in allTasks:
        # First check if the task has timed out (config.py)
        currentTimeInUTC = datetime.datetime.utcnow()
        taskUTCTimout = task['taskCreationTimeInUTC'] + timedelta(hours=int(taskTimeoutAfterCreation))
        if(currentTimeInUTC > taskUTCTimout):
          # update the task status in the database to 'error'
          mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error" } })
          # log error
          writeErrorInfoToTask(task['_id'], "Timeout", "The task {} took too long to complete for job_id: {}".format(str(task['_id']), str(task['job_id'])), mongodb)
          log.warning("[Scheduler] Task timeout. The task {} took too long to complete for job_id: {}".format(str(task['_id']), str(task['job_id'])))

        # ==================================================================================
        # combination 1: taskType == 'startLab' && taskStatus == 'pending'
        # this combination performs the following steps in order to start a lab for a job
        # ==================================================================================
        if((task['taskType'] == "startLab") and (task['taskStatus'] == 'pending')):

          # step 0: most important to prevent infitite crash loops!
          # check if the current task is still valid and has a job associated with it.
          # if this is not done, some information in the task will be 'None', crashing the loop.
          response = checkJobStillInScheduledJobs(task['job_id'], mongodb, log)
          # based on response, if there is no job associated with the task in scheduledJobs, delete it. else continue as normal
          if(response is False):
            # delete the task
            mongodb.tasks.delete_one({ "_id": task['_id'] })
            # exit
            break

          # step 1.1: find a free lab for valid task
          myLab = findFreeLab(task, mongodb)

          # step 1.2 if free lab is None, there are not enough labs available to start a class
          # Note: this can happen throughout the 5th lab starting, meaning the job will be marked as failed but some labs will be up!
          if(myLab is None):
            # add error to task
            writeErrorInfoToTask(task['_id'], "No lab available", "There are not enough labs of environment: '{}' in the database.".format(str(task['environment'])), mongodb)
            # fail the job and delete the task
            # this function is only called when there are no mere labs of the environment required (here)
            # NOTEe: This will cause 'checkJobStillInScheduledJobs' to clean other tasks
            failJobAndDeleteTask(task, mongodb)
            # log
            log.warning("[Scheduler] There are not enough labs of environment: '{}' in the database for job_id: {}".format(str(task['environment']), str(task['job_id'])))
            # break is key in order to prevent crash!
            break

          # step 2: create a task buffer (information to pass into start script / not stored in database)
          # note: there needs to be a second variable for myLab because 'task' is in memory, outdated
          # from 'findFreeLab' method call and 'task' in memory does not contain the lab.
          taskBuffer = generateStartLabTaskBuffer(task, myLab, mongodb)

          # step 3: process the parameters based on their type: list, static, prompt, plugins...
          taskBuffer = processParameters(task, taskBuffer, myLab, mongodb, log)

          # step 3-1: if the above failed (error returned), the taskStatus is now error, so exit out of this if. the task will be cleaned up next cycle.
          if(taskBuffer == "error"):
            break

          # steps 4: extract startScriptName from job
          startScriptName = extractStartScriptName(task, mongodb)

          # steps 5: converting str of the startScriptName into a module
          startScriptNameConverted = customImportModule(startScriptName, task, mongodb, log)

          # step 5.1: if the above fails, mark the task as error
          if(startScriptNameConverted == 'error'):
            # logging
            log.error("[Scheduler] 'customImportModule' failed converting script: {}".format(str(startScriptName)))

            # add error to task
            writeErrorInfoToTask(task['_id'], myLab, "Failed to convert Import Module", mongodb)

            # step 5.2: update the taskStatus to error
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error" } })

            # logging
            log.error("[Scheduler] Failed to start 'startLab' task. task_id: {} for job_id: {}".format(str(task['_id']), str(task['job_id'])))
            break
          # if the 'customImportModule' method worked start a thread with the information generated in previous steps
          else:
            # steps 6: start a thread with the converted 'startScriptNameConverted' module and a main method
            # note: all calls to any external scripts call a method named: main
            threading.Thread(target = startScriptNameConverted.main, args = (taskBuffer,)).start()

            # steps 7: update the taskStatus to running
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "running" } })

            # logging
            log.info("[Scheduler] Starting 'startLab' task. task_id: {} for job_id: {}".format(str(task['_id']), str(task['job_id'])))

        # ======================================================================================================
        # combination 2: taskType == 'startLab' && taskStatus == 'ready'
        # this combination performs the following steps in order finish the task 'startLab' task successfully
        # ======================================================================================================
        elif((task['taskType'] == "startLab") and (task['taskStatus'] == 'ready')):
          # step 1: add the lab to job['labs'] list in scheduledJobs
          addLabToLabsInJob(task, mongodb, log)

          # step 2: add the successInfo to job from task
          addSuccessInfoToJob(task, mongodb)

          # step 3: change that lab status to 'running'
          changeLabStatus(task['lab'], mongodb, 'running', log)

          # logging
          log.info("[Scheduler] Success starting lab. Removing 'startLab' task from database. task_id: {} for job_id: {}".format(str(task['_id']), str(task['job_id'])))

          # step 3: delete the task as its lifecycle is finished
          mongodb.tasks.delete_one({ "_id": task['_id'] })

        # ==============================================================================================================
        # combination 3: taskType == 'startLab' && taskStatus == 'error'
        # this combination performs the following steps in order either retry 'startLab' task with a different lab
        # or mark the job as failed dependng on job['failedAttempts']
        # ==============================================================================================================
        elif((task['taskType'] == "startLab") and (task['taskStatus'] == 'error')):
          # step 1: change the lab status to 'failed'
          changeLabStatus(task['lab'], mongodb, 'failed', log)

          # add the lab to failedLabs in the job
          addTaskLabToFailedLabs(task, mongodb, log)

          # step 2: add the errorInfo to job from task
          addErrorInfoToJob(task, mongodb)

          # logging
          log.warning("[Scheduler] Marking lab: {} as failed. (Failed To Start) for job_id: {}".format(str(task['lab']), str(task['job_id'])))

          # step 2: increase the job['failedAttempts'] counter in 'scheduledJobs' collection by 1
          increaseJobFailedAttemptsCounter(task, mongodb, log)

          # step 3: check if failedAttempts is bigger than limit
          response = checkJobFailedAttemptsCounterIsBigger(task, mongodb)

          # if true, mark the job as failed
          if(response):
            # change the job status to 'failed'
            changeJobStatus(ObjectId(task['job_id']), mongodb, 'failed', log)

            # delete the task as its lifecycle is finished
            mongodb.tasks.delete_one({ "_id": task['_id'] })

            # logging
            log.warning("[Scheduler] Marking job_id: {} as 'failed'. Too many failed attempts.".format(str(task['job_id'])))
          # else retry with a different lab
          else:
            # remove the lab and make the task pending again for boru to allocate and start a new lab
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$unset": {"lab" : 1 }})
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "pending" } })

            # logging
            log.info("[Scheduler] Retrying 'startLab' task. task_id: {} for job_id: {}".format(str(task['_id']), str(task['job_id'])))

        # ===================================================================================
        # combination 4: taskType == 'finishLab' && taskStatus == 'pending'
        # this combination performs the following steps in order to finish a lab for a job
        # ===================================================================================
        elif((task['taskType'] == "finishLab") and (task['taskStatus'] == 'pending')):
          # step 1: create a task buffer (information to pass into finish script / not stored in database)
          taskBuffer = generateFinishLabTaskBuffer(task)

          # step 2: extract finishScriptName from job
          finishScriptName = extractFinishScriptName(task, mongodb)

          # step 3: converting str of the finishScriptName into a module
          finishScriptNameConverted = customImportModule(finishScriptName, task, mongodb, log)
          if(finishScriptNameConverted == 'error'):
            # add error to task
            writeErrorInfoToTask(task['_id'], "LabName", "Failed to convert Import Module", mongodb)

            # step 4: update the taskStatus to error
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error" } })
            # logging
            log.error("[Scheduler] 'customImportModule' failed converting script: {}".format(str(finishScriptName)))
            break
          else:
            # step 5: start a thread with the converted 'finishScriptNameConverted' module and a main method
            # note: all calls to any external scripts call a method named: main
            threading.Thread(target = finishScriptNameConverted.main, args = (taskBuffer,)).start()

            # step 6: update the taskStatus to running
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "running" } })

            # logging
            log.info("[Scheduler] Starting 'finishLab' task. task_id: {} for job_id: {}".format(str(task['_id']), str(task['job_id'])))

        # --------------------------------------------------------------------------------------
        # combination 5: taskType == 'finishLab' && taskStatus == 'ready'
        # this combination performs the following steps in order to finish the task successfully
        # --------------------------------------------------------------------------------------
        elif((task['taskType'] == "finishLab") and (task['taskStatus'] == 'ready')):
          # step 1: push the lab from task['lab'] into job['finishedLabs'] in 'scheduledJobs' collection
          addLabToFinishedLabsInJob(task, mongodb, log)

          # step 2: if this was a finish initiated by the admin('ManualLabFinish' as courseName in the job associated with the task),
          # change the subOrg status to 'cleanupComplete', else mark is as free
          response = checkIfJobIsCleanup(task['job_id'], mongodb)
          if(response):
            changeLabStatus(task['lab'], mongodb, 'cleanupComplete', log)
          else:
            # mark as 'free'
            changeLabStatus(task['lab'], mongodb, 'free', log)
            # chage the lab jobID back to: ""
            mongodb.labs.update_one({ "labName": task['lab'] }, { "$set": { "jobID": " " } })

          # remove the task lab from job['labs'] to prevent issue of re-finishing a successfully finished lab.
          # Original labs are kept in job['originalLabs'], for history references.
          mongodb.scheduledJobs.update_one({ "_id": ObjectId(task['job_id']) }, { "$pull": { "labs": task['lab'] } })

          # logging
          log.info("[Scheduler] Success. Removing 'finishLab' task. task_id: {} for job_id: {}".format(str(task['_id']), str(task['job_id'])))

          # delete the task as its lifecycle is finished
          mongodb.tasks.delete_one({ "_id": task['_id'] })

        # ---------------------------------------------------
        # combination 6: taskType == 'finishLab' && taskStatus == 'error'
        # this combination performs the following steps in order either retry 'finishLab'
        # or mark the job as failed dependng on job['failedAttempts']
        # ---------------------------------------------------
        elif((task['taskType'] == "finishLab") and (task['taskStatus'] == 'error')):

          # logging
          log.warning("[Scheduler] Marking lab: {} as 'failed' (Failed To Finish) for job_id: {}".format(str(task['lab']), str(task['job_id'])))

          # step 1: change the lab status to 'failed'
          changeLabStatus(task['lab'], mongodb, 'failed', log)

          # step 2: add the errorInfo to job from task
          addErrorInfoToJob(task, mongodb)

          # step 3: add the lab to failedLabs in the job
          addTaskLabToFailedLabs(task, mongodb, log)

          # step 4: delete the task as its lifecycle is finished
          mongodb.tasks.delete_one({ "_id": task['_id'] })

        # ------------------------------------------------------------------------------------
        # combination 7: taskType == 'suspendLab' && taskStatus == 'pending'
        # this combination performs the following steps in order to suspend a lab for a job
        # ------------------------------------------------------------------------------------
        elif((task['taskType'] == "suspendLab") and (task['taskStatus'] == 'pending')):
          # step 1: create a task buffer (information to pass into finish script / not stored in database)
          taskBuffer = generateSuspendAndResumeLabTaskBuffer(task)

          # step 2: extract suspendScriptName from job
          suspendScriptName = extractSuspendScriptName(task, mongodb)

          # step 3: converting str of the suspendScriptName into a module
          suspendScriptNameConverted = customImportModule(suspendScriptName, task, mongodb, log)
          if(suspendScriptNameConverted == 'error'):
            # add error to task
            writeErrorInfoToTask(task['_id'], "LabName", "Failed to convert Import Module", mongodb)
            # step 4: update the taskStatus to error
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error" } })
            # logging
            log.error("[Scheduler] 'customImportModule' failed converting script: {}".format(str(suspendScriptName)))
            
            break
          else:
            # step 5: start a thread with the converted 'suspendScriptNameConverted' module and a main method
            # note: all calls to any external scripts call a method named: main
            threading.Thread(target = suspendScriptNameConverted.main, args = (taskBuffer,)).start()

            # step 6: update the taskStatus to running
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "running" } })

            # logging
            log.info("[Scheduler] Starting 'suspendLab' task. task_id: {} for job_id: {}".format(str(task['_id']), str(task['job_id'])))

        # --------------------------------------------------------------------------------------
        # combination 8: taskType == 'suspendLab' && taskStatus == 'ready'
        # this combination performs the following steps in order to finish the task successfully
        # --------------------------------------------------------------------------------------
        elif((task['taskType'] == "suspendLab") and (task['taskStatus'] == 'ready')):

          addLabToSuspendedLabsInJob(task, mongodb, log)

          # step 1: logging
          log.info("[Scheduler] Success. Suspended lab {} for job_id: {}".format(str(task['lab']), str(task['job_id'])))

          # step 2: delete the task as its lifecycle is finished
          mongodb.tasks.delete_one({ "_id": task['_id'] })

        # -------------------------------------------------------------------------------------- !!!
        # combination 9: taskType == 'suspendLab' && taskStatus == 'error'
        # this combination performs the following steps in order to finish the task successfully
        # --------------------------------------------------------------------------------------
        elif((task['taskType'] == "suspendLab") and (task['taskStatus'] == 'error')):

          # logging
          log.error("[Scheduler] Failed to suspend lab {} for job_id: {}".format(str(task['lab']), str(task['job_id'])))

          addErrorInfoToJob(task, mongodb)

          # notification ====================================================================================================================
          jobUpToDate = getJob(task['job_id'], mongodb)
          processNotification("failSuspendNotification", jobUpToDate)
          changeJobStatus(task['job_id'], mongodb, 'running', log)
          # =================================================================================================================================

          # delete the task as its lifecycle is finished
          mongodb.tasks.delete_one({ "_id": task['_id'] })

        # ------------------------------------------------------------------------------------
        # combination 10: taskType == 'resumeLab' && taskStatus == 'pending'
        # this combination performs the following steps in order to suspend a lab for a job
        # ------------------------------------------------------------------------------------
        elif((task['taskType'] == "resumeLab") and (task['taskStatus'] == 'pending')):
          # step 1: create a task buffer (information to pass into finish script / not stored in database)
          taskBuffer = generateSuspendAndResumeLabTaskBuffer(task)

          # step 2: extract suspendScriptName from job
          resumeScriptName = extractResumeScriptName(task, mongodb)

          # step 3: converting str of the resumeScriptName into a module
          resumeScriptNameConverted = customImportModule(resumeScriptName, task, mongodb, log)
          if(resumeScriptNameConverted == 'error'):
            # add error to task
            writeErrorInfoToTask(task['_id'], "LabName", "Failed to convert Import Module", mongodb)
            # step 4: update the taskStatus to error
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error" } })
            # logging
            log.error("[Scheduler] 'customImportModule' failed converting script: {}".format(str(resumeScriptName)))
            break
          else:
            # step 5: start a thread with the converted 'resumeScriptNameConverted' module and a main method
            # note: all calls to any external scripts call a method named: main
            threading.Thread(target = resumeScriptNameConverted.main, args = (taskBuffer,)).start()

            # step 6: update the taskStatus to running
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "running" } })

            # logging
            log.info("[Scheduler] Starting 'resumeLab' task. task_id: {} for job_id: {}".format(str(task['_id']), str(task['job_id'])))

        # --------------------------------------------------------------------------------------
        # combination 11: taskType == 'resumeLab' && taskStatus == 'ready'
        # this combination performs the following steps in order to finish the task successfully
        # --------------------------------------------------------------------------------------
        elif((task['taskType'] == "resumeLab") and (task['taskStatus'] == 'ready')):

          removeLabToSuspendedLabsInJob(task, mongodb, log)

          # step 1: logging
          log.info("[Scheduler] Success. Resumed lab {} for job_id: {}".format(str(task['lab']), str(task['job_id'])))

          # step 2: delete the task as its lifecycle is finished
          mongodb.tasks.delete_one({ "_id": task['_id'] })

        # -------------------------------------------------------------------------------------- !!!
        # combination 12: taskType == 'resumeLab' && taskStatus == 'error'
        # this combination performs the following steps in order to finish the task successfully
        # --------------------------------------------------------------------------------------
        elif((task['taskType'] == "resumeLab") and (task['taskStatus'] == 'error')):

          # step 1: logging
          log.error("[Scheduler] Failed to resume lab {} for job_id: {}".format(str(task['lab']), str(task['job_id'])))

          addErrorInfoToJob(task, mongodb)

          # notification ====================================================================================================================
          jobUpToDate = getJob(task['job_id'], mongodb)
          processNotification("failResumeNotification", jobUpToDate)
          changeJobStatus(task['job_id'], mongodb, 'running', log)
          # =================================================================================================================================

          # step 2: delete the task as its lifecycle is finished
          mongodb.tasks.delete_one({ "_id": task['_id'] })

      # increase cycle and sleep
      cycleCounter = cycleCounter + 1
      time.sleep(5)

    # ================================================
    #       _       _         
    #      | | ___ | |__  ___ 
    #   _  | |/ _ \| '_ \/ __| 
    #  | |_| | (_) | |_) \__ \ 
    #   \___/ \___/|_.__/|___/
    # ================================================
    # JOBS
    # ====

    # each job in 'scheduledJobs' collection either waits for time to start or it is in some stage of running(starting/finishing/etc.)
    # Depending on the status of a job, boru will execute the appropriate code below.
    # once a job is finished, it is archived in order to maintain the database.
    else:
      # getting currentTimeInUTC. this is used
      # note the scheduler runs on UTC time, thats why .utcnow() is used
      currentTimeInUTC = datetime.datetime.utcnow()

      # getting all jobs
      allJobs = getJobs(mongodb, log)

      # looping through each job, depending on job['jobStatus'] run the following code
      for job in allJobs:
        # ----------------------
        # jobStatus == 'pending'
        # ----------------------
        if(job['jobStatus'] == "pending"):
          # if currentTimeInUTC is after job['startDate'], create startLab tasks
          if(currentTimeInUTC >= job['startDate']):
            # create as many startLab tasks depending on job['numberOfLabs'], one task for each lab
            for newTask in range(job['numberOfLabs']):
              # create a new task of type startLab
              createStartLabTask(job, mongodb, log)

            # after the required amount of tasks is created, mark the job as 'starting'
            changeJobStatus(job['_id'], mongodb, 'starting', log)

        # -----------------------
        # jobStatus == 'starting'
        # -----------------------
        elif(job['jobStatus'] == "starting"):
          # check if numberOfLabs == length of job['labs]
          response = checkNumberOfLabsIsEqualToLabs(job['_id'], mongodb)

          # if true, all labs are running therefore mark the job as running
          if(response):
            # change the job status to 'running'
            changeJobStatus(job['_id'], mongodb, 'running', log)
            # notification ====================================================================================================================
            # first get updated info about the job form db
            jobUpToDate = getJob(job['_id'], mongodb)
            processNotification("runningNotification", jobUpToDate)
            # =================================================================================================================================

        # -------------------------
        # jobStatus == 'suspending'
        # -------------------------
        elif(job['jobStatus'] == "suspending"):
          # check if numberOfLabs == length of job['labs]
          response = checkNumberOfLabsIsEqualSuspendedLabs(job['_id'], mongodb)

          # if true, all labs are suspended therefore mark the job as suspended
          if(response):
            # change the job status to 'running'
            changeJobStatus(job['_id'], mongodb, 'suspended', log)
            # notification ====================================================================================================================
            # first get updated info about the job form db
            jobUpToDate = getJob(job['_id'], mongodb)
            processNotification("suspendNotification", jobUpToDate)
            # =================================================================================================================================

        # -----------------------
        # jobStatus == 'resuming'
        # -----------------------
        elif(job['jobStatus'] == "resuming"):
          # check if numberOfLabs == length of job['labs]
          response = checkNumberOfLabsIsEqualZero(job['_id'], mongodb)

          # if true, all labs are running, the suspendedLabs [] is empty therefore mark the job as running
          if(response):
            # change the job status to 'running'
            changeJobStatus(job['_id'], mongodb, 'running', log)
            # notification ====================================================================================================================
            # first get updated info about the job form db
            jobUpToDate = getJob(job['_id'], mongodb)
            processNotification("resumeNotification", jobUpToDate)
            # =================================================================================================================================

        # ----------------------
        # jobStatus == 'running'
        # ----------------------
        elif(job['jobStatus'] == "running"):
          # if currentTimeInUTC is after job['finishDate'], create finishLab tasks for each lab in job['labs'] that are running
          if(currentTimeInUTC >= job['finishDate']):
            # duplicate job['labs'] to job['originalLabs'] to keep track of what labs were used in the past. After every task completes, the Lab will be
            # removed from job['labs'] in order to prevent a situation where one lab fails to finish but the rest are ok. When an admin will 're-finish' the job,
            # all the good-finished labs will be finished again. They could be used by some other job by now. thats why every successfull finish task will remove their
            # lab from job['labs']. to prevent this issue. the job['originalLabs'] will not be used anywhere except an archive reference to keep history of classes.
            duplicateLabsToOriginalLabs(job, mongodb)
            # ####jobStuckResponse = checkIfJobIsStuckFinishing(job['_id'], mongodb, failedToFinishJobTimeout)
            ##### if(jobStuckResponse):
            ####   break
            # create as many finishLab tasks job['labs'], one task for each lab in the list
            for currentLab in job['labs']:
              # create a new task of type finishLab
              createFinishLabTask(job, currentLab, mongodb, log)
            # after the required amount of tasks is created, mark the job as 'finishing'
            changeJobStatus(job['_id'], mongodb, 'finishing', log)

          # look into suspending the job
          # looks ugly I know... it works
          else:
            # check if the class wants to be suspended
            if(job['suspend'] == "yes"):
              # find the suspend time
              for suspendTime in job['listOfSuspendTimes']:
                # narrow down to the day in listOfSuspendTmes
                if(currentTimeInUTC.day == suspendTime.day):
                  # check if it is time to suspend
                  if(currentTimeInUTC >= suspendTime):
                    for lab in job['labs']:
                      createSuspendLabTask(job, lab, mongodb, log)
                    # after the required amount of tasks is created, mark the job as 'suspending'
                    changeJobStatus(job['_id'], mongodb, 'suspending', log)
                    # remove the last suspend time for the job
                    removeLastSuspendTimeFromJob(job['_id'], mongodb, log)
                    break

        # -----------------------
        # jobStatus == 'suspended'
        # -----------------------
        # look into resuming the job
        elif(job['jobStatus'] == "suspended"):
          # find the resume time
          for resumeTime in job['listOfResumeTimes']:
            # narrow down to the day in listOfResumeTimes
            if(currentTimeInUTC.day == resumeTime.day):
              # check if it is time to suspend
              if(currentTimeInUTC >= resumeTime):
                for lab in job['labs']:
                  createResumeLabTask(job, lab, mongodb, log)
                # after the required amount of tasks is created, mark the job as 'suspending'
                changeJobStatus(job['_id'], mongodb, 'resuming', log)
                # remove the last resume time for the job
                removeLastResumeTimeFromJob(job['_id'], mongodb, log)
                break

        # ------------------------
        # jobStatus == 'finishing'
        # ------------------------
        elif(job['jobStatus'] == "finishing"):
          # check if length of job['labs'] == length of job['finishedLabs']
          response = checkNumberOfLabsIsEqualFinishedLabs(job['_id'], mongodb)

          # if true, mark the job as finished
          if(response):
            # change the job status to 'finished'
            changeJobStatus(job['_id'], mongodb, 'finished', log)
          else:
            jobStuckResponse = checkIfJobIsStuckFinishing(job['_id'], mongodb, failedToFinishJobTimeout)

        # -----------------------
        # jobStatus == 'finished'
        # -----------------------
        # archive the job and remove it from 'scheduledJobs' collection
        elif(job['jobStatus'] == "finished"):
          # first get updated info about the job form db (NEEDS To be before archive!)
          jobUpToDate = getJob(job['_id'], mongodb)
          # ---------------------------------------
          archiveJob(job, mongodb, log)
          # notification ====================================================================================================================
          processNotification("finishNotification", jobUpToDate)
          # =================================================================================================================================

        # ---------------------
        # jobStatus == 'failed'
        # ---------------------
        # archive the failed job and remove it from 'scheduledJobs' collection
        elif(job['jobStatus'] == "failed"):
          # first get updated info about the job form db (NEEDS To be before archive!)
          jobUpToDate = getJob(job['_id'], mongodb)
          # ---------------------------------------
          archiveFailedJob(job, mongodb, log)
          # notification ====================================================================================================================
          processNotification("failNotification", jobUpToDate)
          # =================================================================================================================================

      cycleCounter = 0
      # .shutdown() in case of log rotate
      logging.shutdown()
      time.sleep(5)

# ----------------------
# functions from here on
# ----------------------

# this function queries the 'tasks' collection and returns everything there
# parameters:
#  mongodb: allows this function to connect to MongoDB
#  log: allows this function to log
def getTasks(mongodb, log):
  try:
    allTasks = mongodb.tasks.find()
    return allTasks
  except Exception as e:
    # logging
    log.error("[scheduler] Failed to gather all tasks from 'tasks' collection: {}".format(str(e)))

# this function queries the 'scheduledJobs' collection and returns everything there
# parameters:
#  mongodb: allows this function to connect to MongoDB
#  log: allows this function to log
def getJobs(mongodb, log):
  try:
    allJobs = mongodb.scheduledJobs.find()
    return allJobs
  except Exception as e:
    # logging
    log.error("[scheduler] Failed to gather all jobs from 'scheduledJobs' collection: {}".format(str(e)))

# this function queries the 'labs' collection. marks and returns the first lab with status 'free' that it finds
# parameters:
#  task: must contain: task['_id'] - in order to generate a new filed in the task with the lab found
#  mongodb: allows this function to connect to mongo
def findFreeLab(task, mongodb):
  # find a lab with status 'free'
  allLabs = mongodb.labs.find()
  for lab in allLabs:
    if((lab['status'] == 'free') and (lab['environment'] == task['environment'])):
      # modify the lab status to 'starting'
      mongodb.labs.update_one({ "_id": lab['_id'] }, { "$set": { "status": "starting" } })
      # mark the lab with jobID for reference
      mongodb.labs.update_one({ "_id": lab['_id'] }, { "$set": { "jobID": str(task['job_id']) } })
      # add the new found lab to the task
      mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "lab": str(lab['labName'])} })
      # return the labName as the task is now outdated in memory beause a lab was added to DB above
      return str(lab['labName'])
  # None will be returned and looked at after this function call

# this function generates and returns information for a lab task that will be passed into a start script
# parameters:
#  task: must contain: task['_id'], task['lab']
#  myLab: name of the lab (must be a second variable because task is in memory, outdated from 'findFreeLab' method call in main)
def generateStartLabTaskBuffer(task, myLab, mongodb):

  bufferJsonDocument = {"lab": myLab, "parameters": []}

  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      # job info
      bufferJsonDocument.update(courseTemplate = str(job['courseTemplate']))
      bufferJsonDocument.update(sensorTemplate = str(job['sensorTemplate']))
      bufferJsonDocument.update(region = str(job['region']))
      # for stack name
      bufferJsonDocument.update(startDate = str(job['startDate']))
      bufferJsonDocument.update(finishDate = str(job['finishDate']))
      bufferJsonDocument.update(timezone = str(job['timezone']))
      bufferJsonDocument.update(instructor = str(job['instructor']))
      bufferJsonDocument.update(tag = str(job['tag']))
      # task info
      bufferJsonDocument.update(task_id = str(task['_id']))
      bufferJsonDocument.update(sensor = str(task['sensor']))
      bufferJsonDocument.update(courseName = str(task['courseName']))
      bufferJsonDocument.update(courseParameters = str(task['courseParameters']))

  return bufferJsonDocument

# this function generates and returns information for a finishLab task that will be passed into a finish script
# parameters:
#  task: must contain: task['_id'], task['lab'] (no need for a second lab variable as the task is up to date compared to generateStartLabTaskBuffer)
def generateFinishLabTaskBuffer(task):
  bufferJsonDocument = {"lab": str(task['lab'])}
  bufferJsonDocument.update(task_id = str(task['_id']))
  bufferJsonDocument.update(job_id = str(task['job_id']))
  return bufferJsonDocument

# this function generates and returns information for a finishLab task that will be passed into a finish script
# parameters:
#  task: must contain: task['_id'], task['lab'], task['region']
def generateSuspendAndResumeLabTaskBuffer(task):
  bufferJsonDocument = {"lab": str(task['lab'])}
  bufferJsonDocument.update(task_id = str(task['_id']))
  bufferJsonDocument.update(region = str(task['region']))
  bufferJsonDocument.update(job_id = str(task['job_id']))
  return bufferJsonDocument

# this function goes through each parameter and processes it based on its type. Don't touch it
# 'prompt' - looks for the value in scheduled jobs passed in by the user.
# 'static' - uses the value predefined in the courses collection in the database.
# 'list' - same as prompt, only the value entered by the user was checked against a list of valid inputs form the courses collection.
# 'plugin-prompt' - uses the user input to pass into a plugin file, the file generates a new 'processed value' which is used.
# 'plugin-static' - same procedure for plugin as above, but the plugin file uses a value passed in from the database in courses collection, not user prompt.
# 'plugin-list' - same as plugin-prompt, only the value entered by the user was checked against a list of valid inputs form the courses collection.
def processParameters(task, taskBuffer, lab, mongodb, log):
  try:
    # list of all processed parameters to be added into task
    processedParameters = []
    # go through each parameter in taskBuffer['courseParameters']
    # https://stackoverflow.com/questions/1894269/convert-string-representation-of-list-to-list

    taskBufferParameters = taskBuffer.get("courseParameters")
    # converting a str into a list
    taskBufferParameters = ast.literal_eval(taskBufferParameters)

    for parameter in taskBufferParameters:
      # if 'paramType' == 'prompt'
      if(str(parameter['paramType']) == "prompt"):
        # get the Key of the parameter
        paramKey = parameter['paramKey']
        # get the Value of the parameter from a field in job named the same as 'parameter['paramKey']'
        paramValue = processPromptValue(paramKey, task, mongodb, log)
        # append paramKey and paramValue to 'processedParameters' list
        processedParameters.append({paramKey : paramValue})

      # elif 'paramType' == 'static'
      elif(str(parameter['paramType']) == "static"):
        # get the Key of the parameter
        paramKey = parameter['paramKey']
        # get the static Value of the parameter stored in DB as it is static
        paramValue = parameter['paramValue']
        # append paramKey and paramValue to 'processedParameters' list
        processedParameters.append({paramKey : paramValue})

      # elif 'paramType' == 'list'
      elif(str(parameter['paramType']) == "list"):
        # the value has been allready validated when making the request so it is very similar to 'prompt'
        # get the Key of the parameter
        paramKey = parameter['paramKey']
        # get the Value of the parameter from a field in job named the same as 'parameter['paramKey']'
        paramValue = processPromptValue(paramKey, task, mongodb, log)
        # append paramKey and paramValue to 'processedParameters' list
        processedParameters.append({paramKey : paramValue})

      # elif 'paramType' == 'plugin-prompt'
      elif(str(parameter['paramType']) == "plugin-prompt"):
        # get the Key of the parameter
        paramKey = parameter['paramKey']
        # get the Value of the parameter from a field in job named the same as 'parameter['paramKey']'
        paramUnprocessedValue = processPromptValue(paramKey, task, mongodb, log)
        # get the paramFile as it is required to process the plugin
        paramFile = parameter['paramFile']
        # now run and process the parameter as it is a plugin
        paramValue = processPlugin(paramFile, paramKey, paramUnprocessedValue, task, lab)

        for key in paramValue:
          value = paramValue[key]
          # if error returned from plugin, fail task and log error
          if(checkParamValueForError(key)):
            # log error
            log.error("[Scheduler] Failed to process plugin parameter: {}. Plugin response: {}. Task_id: {}".format(str(parameter['paramKey']), str(value), str(task['_id'])))
            # add error to task
            writeErrorInfoToTask(task['_id'], lab, str(value), mongodb)
            # mark task as error
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error"}})
            log.error("[Scheduler] Marked task as 'error'.")
            # return
            return("error")
          # append paramKey and paramValue to 'processedParameters' list
          processedParameters.append({paramKey : value})
          break

      # elif 'paramType' == 'plugin-static'
      elif(str(parameter['paramType']) == "plugin-static"):
        # get the Key of the parameter
        paramKey = parameter['paramKey']
        # get the paramFile as it is required to process the plugin
        paramFile = parameter['paramFile']
        # get the static Value of the parameter stored in DB as it is static
        paramUnprocessedValue = parameter['paramValue']
        # now run and process the parameter as it is a plugin
        paramValue = processPlugin(paramFile, paramKey, paramUnprocessedValue, task, lab)

        for key in paramValue:
          value = paramValue[key]
          # if error returned from plugin, fail task and log error
          if(checkParamValueForError(key)):
            # log error
            log.error("[Scheduler] Failed to process plugin parameter: {}. Plugin response: {}. Task_id: {}".format(str(parameter['paramKey']), str(value), str(task['_id'])))
            # add error to task
            writeErrorInfoToTask(task['_id'], lab, str(value), mongodb)
            # mark task as error
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error"}})
            log.error("[Scheduler] Marked task as 'error'. Task_id: {}".format(str(task['_id'])))
            # return
            return("error")
          # append paramKey and paramValue to 'processedParameters' list
          processedParameters.append({paramKey : value})
          break

      # elif 'paramType' == 'plugin-list'
      elif(str(parameter['paramType']) == "plugin-list"):
        # the value has been allready validated when making the request so it is very similar to 'plugin-prompt'. the user input must be used to process the plugin
        # get the Key of the parameter
        paramKey = parameter['paramKey']
        # get the paramFile as it is required to process the plugin
        paramFile = parameter['paramFile']
        # get the Value of the parameter from a field in job named the same as 'parameter['paramKey']'
        paramUnprocessedValue = processPromptValue(paramKey, task, mongodb, log)
        # get the paramFile as it is required to process the plugin
        paramFile = parameter['paramFile']
        # now run and process the parameter as it is a plugin
        paramValue = processPlugin(paramFile, paramKey, paramUnprocessedValue, task, lab)

        for key in paramValue:
          value = paramValue[key]
          # if error returned from plugin, fail task and log error
          if(checkParamValueForError(key)):
            # log error
            log.error("[Scheduler] Failed to process plugin parameter: {}. Plugin response: {}. Task_id: {}".format(str(parameter['paramKey']), str(value), str(task['_id'])))
            # add error to task
            writeErrorInfoToTask(task['_id'], lab, str(value), mongodb)
            # mark task as error
            mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error"}})
            log.error("[Scheduler] Marked task as 'error'. Task_id: {}".format(str(task['_id'])))
            # return
            return("error")
          # append paramKey and paramValue to 'processedParameters' list
          processedParameters.append({paramKey : value})
          break

    taskBuffer['parameters'].append(processedParameters)
    # update parameters
    mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "parameters": processedParameters}})
    # courseParameters are no longer used. instead, 'parameters' are used when starting a lab
    # .....
    return taskBuffer
  except Exception as e:
    # log error
    log.error("[Scheduler] Failed to process plugin parameter. Task_id: {}. Error: {}".format(str(task['_id']), str(e)))
    # add error to task
    writeErrorInfoToTask(task['_id'], lab, str(e), mongodb)
    # mark task as error
    mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error"}})
    log.error("[Scheduler] Marked task as 'error'. Task_id: {}".format(str(task['_id'])))
    # return
    return("error")

# write the error to the task in order for it to be written to the job
def writeErrorInfoToTask(task_id, accountName, error, mongodb):
  mongodb.tasks.update_one({ "_id": task_id }, { "$push": { "errorInfo": accountName } })
  mongodb.tasks.update_one({ "_id": task_id }, { "$push": { "errorInfo": str(error) } })

# check if the value passed in is 'error'
def checkParamValueForError(paramValue):
  if(paramValue == "error"):
    return True
  return False

# import and run the plugin (or script) and return its response in JSON
def processPlugin(paramFile, paramKey, paramValue, task, lab):
  # convert str of paramFile into a callable module
  try:
    moduleString = "scripts." + str(paramFile)
    pluginNameModule = import_module(str(moduleString))
  except:
    moduleString = "plugins." + str(paramFile)
    pluginNameModule = import_module(str(moduleString))

  # get the processed response Value from the plugin
  pluginResponse = pluginNameModule.getIdentifier(lab, task["region"], paramValue)
  # converting the str variable into a dict
  pluginResponseInJson = json.loads(pluginResponse)
  return pluginResponseInJson

# process a value entered by a user when requesting the job. The value will be under the paramKey Key in job JSON.
def processPromptValue(paramKey, task, mongodb, log):
  allJobs = getJobs(mongodb, log)
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      for jobParam in job:
        if(str(jobParam) == str(paramKey)):
          paramValue = job[jobParam]
          return paramValue


# this function creates a new startLab task with the information contained in this method
# parameters:
#  job: to extract relevant information about the job
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def createStartLabTask(job, mongodb, log):

  taskCreationTimeInUTC = datetime.datetime.utcnow()

  startLabTaskBuffer = {"job_id": str(job['_id'])}

  courseParameters = []

  jobCourseInformation = mongodb.courses.find_one({"courseName" : job['courseName']})

  for paramObject in jobCourseInformation['cloudFormationParameters']:
    courseParameters.append(paramObject)

  startLabTaskBuffer.update(courseParameters = courseParameters)

  startLabTaskBuffer.update(taskType = "startLab")
  startLabTaskBuffer.update(region = str(job['region']))
  startLabTaskBuffer.update(sensor = str(job['sensor']))
  startLabTaskBuffer.update(courseName = str(job['courseName']))
  startLabTaskBuffer.update(environment = str(job['environment']))
  startLabTaskBuffer.update(taskStatus = "pending")
  startLabTaskBuffer.update(successInfo = [])
  startLabTaskBuffer.update(errorInfo = [])
  startLabTaskBuffer.update(taskCreationTimeInUTC = taskCreationTimeInUTC)
  
  # mongodb
  mongodb.tasks.insert_one(startLabTaskBuffer)
  # logging
  log.info("[Scheduler] Created 'startLab' task for job: {} job_id: {}".format(str(job['tag']), str(job['_id'])))

# this function creates a new finishLab task with the information contained in this method
# parameters:
#  job: to extract relevant information about the job into
#  lab: the lab name to suspend
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def createFinishLabTask(job, currentLab, mongodb, log):
  taskCreationTimeInUTC = datetime.datetime.utcnow()

  startLabTaskBuffer = {"job_id": str(job['_id'])}
  startLabTaskBuffer.update(taskType = "finishLab")
  startLabTaskBuffer.update(lab = str(currentLab))
  startLabTaskBuffer.update(taskStatus = "pending")
  startLabTaskBuffer.update(errorInfo = [])
  startLabTaskBuffer.update(taskCreationTimeInUTC = taskCreationTimeInUTC)
  # mongodb
  mongodb.tasks.insert_one(startLabTaskBuffer)
  # logging
  log.info("[Scheduler] Created 'finishLab' task for job: {} job_id: {}".format(str(job['tag']), str(job['_id'])))


# this function creates a new suspendLab task
# parameters:
#  job: to extract relevant information about the job
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def createSuspendLabTask(job, lab, mongodb, log):
  taskCreationTimeInUTC = datetime.datetime.utcnow()

  suspendLabTaskBuffer = {"job_id": str(job['_id'])}
  suspendLabTaskBuffer.update(region = str(job['region']))
  suspendLabTaskBuffer.update(lab = lab)
  suspendLabTaskBuffer.update(taskType = "suspendLab")
  suspendLabTaskBuffer.update(taskStatus = "pending")
  suspendLabTaskBuffer.update(errorInfo = [])
  suspendLabTaskBuffer.update(taskCreationTimeInUTC = taskCreationTimeInUTC)
  # mongodb
  mongodb.tasks.insert_one(suspendLabTaskBuffer)
  # logging
  log.info("[Scheduler] Created 'suspendLab' task for job: {} job_id: {}".format(str(job['tag']), str(job['_id'])))

# this function creates a new suspendLab task
# parameters:
#  job: to extract relevant information about the job
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def createResumeLabTask(job, lab, mongodb, log):
  taskCreationTimeInUTC = datetime.datetime.utcnow()

  resumeLabTaskBuffer = {"job_id": str(job['_id'])}
  resumeLabTaskBuffer.update(region = str(job['region']))
  resumeLabTaskBuffer.update(lab = lab)
  resumeLabTaskBuffer.update(taskType = "resumeLab")
  resumeLabTaskBuffer.update(taskStatus = "pending")
  resumeLabTaskBuffer.update(errorInfo = [])
  resumeLabTaskBuffer.update(taskCreationTimeInUTC = taskCreationTimeInUTC)
  # mongodb
  mongodb.tasks.insert_one(resumeLabTaskBuffer)
  # logging
  log.info("[Scheduler] Created 'resumeLab' task for job: {} job_id: {}".format(str(job['tag']), str(job['_id'])))

# this function extracts the startScriptName from 'scheduledJobs' collection using the job id from the task that is passed in
# parameters:
#  task: must contain: task['job_id']
#  mongodb: allows this function to connect to mongo
def extractStartScriptName(task, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      return job['startScriptName']

# this function extracts the finishScriptName from 'scheduledJobs' collection using the job id from the task that is passed in
# parameters:
#  task: must contain: task['job_id']
#  mongodb: allows this function to connect to mongo
def extractFinishScriptName(task, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      return job['finishScriptName']

# this function extracts the suspendScriptName from 'scheduledJobs' collection using the job id from the task that is passed in
# parameters:
#  task: must contain: task['job_id']
#  mongodb: allows this function to connect to mongo
def extractSuspendScriptName(task, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      return job['suspendScriptName']

# this function extracts the resumeScriptName from 'scheduledJobs' collection using the job id from the task that is passed in
# parameters:
#  task: must contain: task['job_id']
#  mongodb: allows this function to connect to mongo
def extractResumeScriptName(task, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      return job['resumeScriptName']


# this function appends task['lab'] into job['labs'] in 'scheduledJobs' collection using task['job_id']
# parameters:
#  task: must contain: task['job_id'], task['lab']
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def addLabToLabsInJob(task, mongodb, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      mongodb.scheduledJobs.update_one({ "_id": job['_id'] }, { "$push": { "labs": str(task['lab'])} })
      # logging
      log.info("[Scheduler] Adding lab: {} to job. job_id: {}".format(str(task['lab']), str(task['job_id'])))
      break

# this function appends task['lab'] into job['finishedLabs'] in 'scheduledJobs' collection using task['job_id']
# parameters:
#  task: must contain: task['job_id'], task['lab']
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def addLabToFinishedLabsInJob(task, mongodb, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      mongodb.scheduledJobs.update_one({ "_id": job['_id'] }, { "$push": { "finishedLabs": str(task['lab'])} })
      # logging
      log.info("[Scheduler] Adding lab: {} to 'finishedLabs'. job_id: {}".format(str(task['lab']), str(task['job_id'])))
      break

# This function takes in a task, extract the lab in that task and pushes the lab into suspended labs in job
def addLabToSuspendedLabsInJob(task, mongodb, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      mongodb.scheduledJobs.update_one({ "_id": job['_id'] }, { "$push": { "suspendedLabs": str(task['lab'])} })
      # logging
      log.info("[Scheduler] Adding lab: {} to 'suspendedLabs'. job_id: {}".format(str(task['lab']), str(task['job_id'])))
      break

# This function takes in a task, extract the lab in that task and pulls the lab from suspended labs in job
def removeLabToSuspendedLabsInJob(task, mongodb, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      mongodb.scheduledJobs.update_one({ "_id": job['_id'] }, { "$pull": { "suspendedLabs": str(task['lab'])} })
      # logging
      log.info("[Scheduler] Removing lab: {} from 'suspendedLabs'. job_id: {}".format(str(task['lab']), str(task['job_id'])))
      break

# This function removes the last resume time from the job['listOfResumeTimes']. The resume times are generated in order. Care when manually adding resume times
def removeLastResumeTimeFromJob(jobID, mongodb, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(jobID)):
      mongodb.scheduledJobs.update_one({ "_id": ObjectId(job['_id']) }, { "$pop": { "listOfResumeTimes": 1 } })
      # logging
      log.info("[Scheduler] Removing last 'listOfResumeTimes' element from job_id: {}".format(str(jobID)))
      break

# This function removes the last suspend time from the job['listOfSuspendTimes']. The suspend times are generated in order. Care when manually adding suspend times
def removeLastSuspendTimeFromJob(jobID, mongodb, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(jobID)):
      mongodb.scheduledJobs.update_one({ "_id": ObjectId(job['_id']) }, { "$pop": { "listOfSuspendTimes": 1 } })
      # logging
      log.info("[Scheduler] Removing last 'listOfSuspendTimes' element from job_id: {}".format(str(jobID)))
      break

# this function changes the status of a lab in 'labs' collection
# it uses the lab name passed in along with a new status also passed in to determine what lab to change and to what new status
# parameters:
#  labToModify: the name of the lab that will be modified
#  mongodb: allows this function to connect to mongo
#  newStatus: the name of the new status for the lab
#  log: allows this function to log
def changeLabStatus(labToModify, mongodb, newStatus, log):
  allLabs = mongodb.labs.find()
  for lab in allLabs:
    if(lab['labName'] == str(labToModify)):
      # modify the lab
      mongodb.labs.update_one({ "_id": lab['_id'] }, { "$set": { "status": newStatus } })
      # logging
      log.info("[Scheduler] Changing lab Status to: '{}' for lab. labName: {}".format(newStatus, str(lab['labName'])))
      break

# this function changes the status of a job in 'scheduledJobs' collection
# it uses the job id passed in along with a new status also passed in
# parameters:
#  job_id: the id on the job
#  mongodb: allows this function to connect to mongo
#  newStatus: the name of the new status for the job
#  log: allows this function to log
def changeJobStatus(job_id, mongodb, newStatus, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(job_id)):
      mongodb.scheduledJobs.update_one({ "_id": job['_id'] }, { "$set": { "jobStatus": newStatus} })
      # logging
      log.info("[Scheduler] Changing 'jobStatus' to: '{}' for job. job_id: {}".format(newStatus, str(job['_id'])))
      break

# converting str of the scriptName into a runnable module
def customImportModule(scriptName, task, mongodb, log):
  try:
    try:
      moduleString = "scripts." + str(scriptName)
      scriptNameConvertedToModule = import_module(str(moduleString))
    except:
      moduleString = "plugins." + str(scriptName)
      scriptNameConvertedToModule = import_module(str(moduleString))
    # return the module
    return scriptNameConvertedToModule
  except Exception as e:
    # logging
    log.warning("[Scheduler] Failed to convert and import module for task. Error: {}".format(str(e)))
    # delete the task as its lifecycle is finished
    mongodb.tasks.update_one({ "_id": task['_id'] }, { "$set": { "taskStatus": "error" } })
    # logging
    log.warning("[Scheduler] Marking '{}' task. as error: {}".format(str(task['taskType']), str(task['_id'])))
    return ("error")

# this function increases the 'failedAttempts' field by 1 of a job task['job_id'] in the 'scheduledJobs' collection
# parameters:
#  task: must contain: task['job_id']
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def increaseJobFailedAttemptsCounter(task, mongodb, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      # get the number
      numberOfFailedAttempts = job["failedAttempts"]
      # add +1 to numberOfFailedAttempts
      numberOfFailedAttempts = numberOfFailedAttempts + 1
      # modify the job
      mongodb.scheduledJobs.update_one({ "_id": job['_id'] }, { "$set": { "failedAttempts": int(numberOfFailedAttempts)} })
      # logging
      log.info("[Scheduler] Changing 'numberOfFailedAttempts' to: {} for job. job_id: {}".format(str(numberOfFailedAttempts), str(job['_id'])))

# this function checks if 'failedAttempts' field is bigger than the limit specified. if so, it returns True
# parameters:
#  task: must contain: task['job_id']
#  mongodb: allows this function to connect to mongo
def checkJobFailedAttemptsCounterIsBigger(task, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(task['job_id'])):
      # get the number
      numberOfFailedAttempts = job["failedAttempts"]
      # check
      if(int(numberOfFailedAttempts) >= 5):
        return True
      else:
        return False

# this function checks if the length of the 'labs' list field in 'scheduledJobs' collection is
# the same as the 'numberOfLabs' field. the job id passed in in order to fing the job in question
# parameters:
#  job_id: the id of the job to be checked
#  mongodb: allows this function to connect to mongo
def checkNumberOfLabsIsEqualToLabs(job_id, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(job_id)):
      numberOfLabs = job['numberOfLabs']
      if(numberOfLabs == len(job['labs'])):
        return True
      else:
        return False

# this function checks if the length of the job['labs'] array filed is the same as
# the length of job['finishedLabs'] array field in order to confirm all the labs are finished
# (job['finishedLabs'] is updated once a finishLab task successfully finishes. if not, the task itself changes the job['jobStatus'] to failed)
# parameters:
#  job_id: the id of the job to be checked
#  mongodb: allows this function to connect to mongo
def checkNumberOfLabsIsEqualFinishedLabs(job_id, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(job_id)):
      if(len(job['finishedLabs']) >= int(job['numberOfLabs'])):
        return True
      else:
        return False

# this function checks if the length of job['suspendedLabs'] == length of job['labs']
def checkNumberOfLabsIsEqualSuspendedLabs(job_id, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(job_id)):
      if(len(job['labs']) == len(job['suspendedLabs'])):
        return True
      else:
        return False

# this function checks if the length of job['suspendedLabs'] == 0
def checkNumberOfLabsIsEqualZero(job_id, mongodb):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(job_id)):
      if(len(job['suspendedLabs']) == 0):
        return True
      else:
        return False

# this function moves the whole job and inserts its information into 'archivedJobs' collection.
# it also delets the job from the 'scheduledJobs' collection
# parameters:
#  job: the whole job and its information
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def archiveJob(job, mongodb, log):
  try:
    # Move the job(scheduledJob) into the archivedJobs Collection
    mongodb.archivedJobs.insert_one(job)
  except Exception as e:
    log.exception("Failed to archive job")
    # mark the job as Failed to archive
    changeJobStatus(job['_id'], mongodb, 'failedToArchive', log)
    # exit
    return
  # Delete the job(scheduledJob) from scheduledJobs Collection
  mongodb.scheduledJobs.delete_one({ "_id" : ObjectId(str(job['_id'])) })
  # logging
  log.info("[Scheduler] Archived job to archivedJobs collection. job_id: {}".format(str(job['_id'])))

# this function moves the whole job and inserts its information into 'failedJobs' collection.
# it also delets the job from the 'scheduledJobs' collection
# parameters:
#  job: the whole job and its information
#  mongodb: allows this function to connect to mongo
#  log: allows this function to log
def archiveFailedJob(job, mongodb, log):
  # add a cleanedUp variable and set it to false, this is used to indicate is some labs will be running
  #mongodb.scheduledJobs.update_one({ "_id": job['_id'] }, { "$set": { "cleanedUp": "no" } })
  # Move the job(scheduledJob) into the archivedJobs Collection
  try:
    mongodb.failedJobs.insert_one(job)
  except Exception as e:
    log.exception("Failed to archive failed job")
    # mark the job as Failed to archive
    changeJobStatus(job['_id'], mongodb, 'failedToArchive', log)
    # exit
    return
  # Delete the job(scheduledJob) from scheduledJobs Collection
  mongodb.scheduledJobs.delete_one({ "_id" : ObjectId(str(job['_id'])) })
  # logging
  log.info("[Scheduler] Moved job to failedJobs collection. job_id: {}".format(str(job['_id'])))

# this function looks at the job_id in the task and compares is with all jobs in scheduledJobs collection.
# if the job with task job_id is in scheduledJobs, all good. else, return False
def checkJobStillInScheduledJobs(taskJobId, mongodb, log):
  allJobs = mongodb.scheduledJobs.find()
  for job in allJobs:
    if(str(job['_id']) == str(taskJobId)):
      return True
  log.warning("[Scheduler] the job for current task no longer exists.")
  return False

# This function extracts the task['lab'] and pushes it to job['failedLabs']
def addTaskLabToFailedLabs(task, mongodb, log):
  currentTask = mongodb.tasks.find_one({ "_id": ObjectId(str(task['_id']))}, { "lab":1, "_id":0 })
  for i in currentTask:
    taskLab = currentTask[i]
    break
  mongodb.scheduledJobs.update_one({"_id": ObjectId(str(task['job_id']))}, { "$push": { "failedLabs": str(taskLab)}})

# this function marks the job as failed and delets the task that noticed there are no more labs available for the environment.
def failJobAndDeleteTask(task, mongodb):
  # try because many tasks could be allready running
  try:
    # need to get the job of this task
    allJobs = getJobs(mongodb, log)
    for job in allJobs:
      if(str(job['_id']) == str(task['job_id'])):
        # mark the whole job as failed and send notify email
        # change the job status to 'failed'
        changeJobStatus(job['_id'], mongodb, 'failed', log)
        # notification ============================================================================================================
        processNotification("failNotification", job)
        # =========================================================================================================================
        # archive the job to prevent a loop of notifications for each lab. Key step. the left-over tasks will be deleted as usual
        archiveFailedJob(job, mongodb, log)
        # delete the task as its lifecycle is finished
        mongodb.tasks.delete_one({ "_id": task['_id'] })
        break
  except:
    pass

# Add success info from task to job
def addSuccessInfoToJob(task, mongodb):
  mongodb.scheduledJobs.update_one({ "_id": ObjectId(task['job_id']) }, { "$push": { "successInfo": task['successInfo'] } })

# Add error info from task to job
def addErrorInfoToJob(task, mongodb):
  mongodb.scheduledJobs.update_one({ "_id": ObjectId(task['job_id']) }, { "$push": { "errorInfo": task['errorInfo'] } })

# This function checks if a job is ninishing for more than X hours (specified in config.py) and marks it as 'failedToFinish' if that's True
def checkIfJobIsStuckFinishing(jobId, mongodb, failedToFinishJobTimeout):
  # get the job
  allJobs = getJobs(mongodb, log)
  for job in allJobs:
    if(str(job['_id']) == str(jobId)):
      # if there is still anything in the labs [] list not finished
      if(job['labs']):
        # get current time
        currentTimeInUTC = datetime.datetime.utcnow()
        jobUTCTimout = job['finishDate'] + timedelta(hours=int(failedToFinishJobTimeout))
        # check for timeout. if the finishdate + 1 hour is bigger then current time
        if(currentTimeInUTC > jobUTCTimout):
          # if yes, change the job status to 'failedToFinish'
          changeJobStatus(job['_id'], mongodb, 'failedToFinish', log)
          mongodb.scheduledJobs.update_one({ "_id": ObjectId(str(jobId)) }, { "$push": { "errorInfo": ["Job Timeout", "The job has failed because it timed out after {} hour(s) of finishing.".format(str(failedToFinishJobTimeout))] } })
          # notification ====================================================================================================================
          jobUpToDate = getJob(jobId, mongodb)
          processNotification("failFinishNotification", jobUpToDate)
          # =================================================================================================================================
          return True
  return False

# Calls a notification plugin and does not wait for a response
def processNotification(notificationAction, job):
  try:
    # there are 5 possible notificationActions:
    #   1. runningNotification
    #   2. suspendNotification
    #   3. resumeNotification
    #   4. finishNotification
    #   5. failNotification - send when the whole job fails
    #   6. failSuspendNotification - send when suspending timeout is reached
    #   7. failResumeNotification - send when suspending timeout is reached
    #   8. failFinishNotification - send when a labFinish Fails

    #   8. failFinishNotification - send when lab fails to finish
    # Note: for the combination: taks['taskType'] == 'finishLab' and taks['taskStatus'] == 'error',
    # the notification['job'] passed into the notification script is only the lab name!
    # Keep in mind when creating notifications with this combination.

    # there are 3 possible types for each notification:
    #   1. static - read the recipients and files directly from the database
    #   2. prompt - the user input stored in job will be used for recipients and files
    #   3. list   - same as prompt but only inputs from user which are in 'validInput' are valid

    # when a notification is called, 'notificationFile' is used
    # a notification call (this function in boru) takes in:

    # all the notifications(recipients and files) will be appended to the job
    # everythong from the job will be used. not form db.courses as job contains user input
    # ==================================================================================================
    # code:
    for notification in job['notifications']:
      if(str(notification['notificationAction']) == str(notificationAction)):
        # extract th info
        notificationFileName = notification['notificationFile']
        notificationRecipients = notification['recipients']
        # need to convert a str to actual module to run
        moduleString = "notificationPlugins." + str(notificationFileName)
        notificationFileNameConverted = import_module(str(moduleString))
        message = notification['notificationAction']

        # logging
        log.info("[Scheduler] About to send Notification...")
        # run the notification (each notify function will be: notify(recipient, job, message))
        threading.Thread(target = notificationFileNameConverted.notify, args = (notificationRecipients,job,message,)).start()
        # logging
        log.info("[Scheduler] Handed '{}' Notification to: '{}'".format(str(notification['notificationAction']), str(notificationFileName)))
  except Exception as e:
    log.exception("[Scheduler] Function processNotification Failed.")

# used before every notification to pass in the most up to date job
# Note: when archiving, make sure to call this function before archive methods like archiveJob() as the job will be moved.
def getJob(job_id, mongodb):
  # get all jobs
  allJobs = mongodb.scheduledJobs.find()
  # look for the same _id
  for job in allJobs:
    if(str(job['_id']) == str(job_id)):
      # return the job with up to date information
      return job
  return("Internal Error!: No job found!")

# get the labs and copy them to originalLabs
def duplicateLabsToOriginalLabs(job, mongodb):
  # insert a new [ ] of originalLabs
  mongodb.scheduledJobs.update_one({"_id" : job['_id']}, {"$set" : {"originalLabs": job['labs']}})

# checks if 'ManualLabFinish' is the 'courseName' in the job with the id passed into this method
def checkIfJobIsCleanup(jobId, mongodb):
  # get all jobs
  allJobs = mongodb.scheduledJobs.find()
  # look for the one with 'jobId'
  for job in allJobs:
    if(str(job['_id']) == str(jobId)):
      # return true or false if the 'courseName' == 'ManualLabFinish'
      if(str(job['courseName']) == "ManualLabFinish"):
        return True
      else:
        return False
      break
  # if not found for some reason, just default to a normal class not a cleanup class
  return False

# -----
# start
if __name__ == '__main__':
  main()
