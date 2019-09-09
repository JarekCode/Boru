#!/usr/bin/python3
# -*- coding: utf-8 -*-

# -------------------------------------------
# Name: YOUR NAME
# Version: 0.1
# Notes: No return required. ADD UPDATES HERE
# -------------------------------------------

# --------------------
# Notification Actions
# --------------------
# There are 8 possible notificationActions: Each notification should account for all of them.
#  1. runningNotification - Sent after ALL labs are up. The jobStatus is set to running.
#  2. suspendNotification - Sent after ALL labs are suspended. The jobStatus is set to suspended.
#  3. resumeNotification - Sent after  ALL labs are resumed. The jobStatus is set back to running.
#  4. finishNotification - Sent after ALL labs are finished. The jobStatus is set to finished.
#  5. failNotification - Sent after the limit of failures is reached when job tried to start. The jobStatus is set to failed.
#  6. failSuspendNotification - Sent after ONE lab fails to suspend.
#  7. failResumeNotification - Sent after ONE lab fails to resume.
#  8. failFinishNotification - Sent after the Job fails to finish (Some lab failed to finish or all labs took too long to finish - timeout)

# Imports
import json

# --------------------------------
# notify - Called by the scheduler
# --------------------------------
# recipient - One or many recipients. If many, a ['list'] is passed in, else a 'String'
# job - The full job passed in from the MongoDB 'scheduledJobs' Collection.
# message - The type of the notification. See above 'Notification Actions'
def notify(recipient, job, message="Notification from Boru"):

  # -----------------------------------------------------------------------------------------
  # EXAMPLE: How to distinguish between 'recipient' list and string. (One vs Many recipients)
  if(isinstance(recipient, list)):
    manyRecipients = ", ".join(recipient)
  else:
    oneRecipient = recipient
  # -----------------------------------------------------------------------------------------

  # ===================
  # runningNotification
  # ===================
  if(message == "runningNotification"):
    pass # YOUR CODE HERE

  # ===================
  # suspendNotification
  # ===================
  elif(message == "suspendNotification"):
    pass # YOUR CODE HERE

  # ==================
  # resumeNotification
  # ==================
  elif(message == "resumeNotification"):
    pass # YOUR CODE HERE

  # ==================
  # finishNotification
  # ==================
  elif(message == "finishNotification"):
    pass # YOUR CODE HERE

  # ================
  # failNotification
  # ================
  elif(message == "failNotification"):
    pass # YOUR CODE HERE

  # =======================
  # failSuspendNotification
  # =======================
  elif(message == "failSuspendNotification"):
    pass # YOUR CODE HERE

  # =======================
  # failResumeNotification
  # =======================
  elif(message == "failResumeNotification"):
    pass # YOUR CODE HERE

  # =======================
  # failFinishNotification
  # =======================
  elif(message == "failFinishNotification"):
    pass # YOUR CODE HERE

  # ==========================
  # Other Unknown Notification
  # ==========================
  # Will never happen unless the scheduler is updated.
  # Add a generic response here.
  else:
    pass # YOUR CODE HERE
