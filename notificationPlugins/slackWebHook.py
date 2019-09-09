#!/usr/bin/env python3
# ------------------
# Jaroslaw Glodowski
# ------------------
# ---------------------------------------------------
# slackWebHook.py |  Used to test send information to a the slack room boru in alien-training
# ---------------------------------------------------
# Slack messaging formatting - https://api.slack.com/messaging/composing

# There are 8 possible notificationActions:
  #  1. runningNotification - Sent after ALL labs are up. The jobStatus is set to running.
  #  2. suspendNotification - Sent after ALL labs are suspended. The jobStatus is set to suspended.
  #  3. resumeNotification - Sent after  ALL labs are resumed. The jobStatus is set back to running.
  #  4. finishNotification - Sent after ALL labs are finished. The jobStatus is set to finished.
  #  5. failNotification - Sent after the limit of failures is reached when job tried to start. The jobStatus is set to failed.
  #  6. failSuspendNotification - Sent after ONE lab fails to suspend.
  #  7. failResumeNotification - Sent after ONE lab fails to resume.
  #  8. failFinishNotification - Sent after ONE lab fails to finish.

import requests
import json
import logging
import datetime

# This is needed to import the boru python config file
import sys
sys.path.insert(0, '/etc/boru/')
import config

logging.basicConfig(filename='/var/log/boru.log',level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")
log = logging.getLogger('boru')

def notify(recipient, job, notificationAction="Notification from Boru"):
  if recipient == "Boru":
    url = config.getConfig("slackBoruURL")
  else:
    log.error("[slackWebHook] " + str(recipient) + " unknown")
    exit()

  # info from job
  courseName = job['courseName']
  instructor = job['instructor']
  tag = job['tag']
  labs = job['labs']
  information = job['successInfo']
  errorInformation = job['errorInfo']
  _id = job['_id']

  # ----------------------------------------------------------------------------------------
  # Running Notification
  # ----------------------------------------------------------------------------------------
  if(notificationAction == "runningNotification"):
    customMessage = \
".\n\n\n\n\n------\n\
*Boru* :alien:\n\
------\n\n\
*{}* class: *{}* for *{}* is now Running.\n\n\
<https://boruLink.com/viewJob/{}>\n\
*Accounts:*\n\
{}\n\n\
\n*Account Information:*\n".format(str(courseName), str(tag), str(instructor), str(_id), str(labs))
    for i in job['successInfo']:
      customMessage = customMessage + "\n*Account :* {}".format(str(i[0]).lower())
      for j in i[1]:
        customMessage = customMessage + "\n*{} :* {}".format(str(j['OutputKey']), str(j['OutputValue']))
      customMessage = customMessage + "\n"
    customMessage = customMessage + "\n\n*Instructor :* {}".format(str(job['instructor']))
    customMessage = customMessage + "\n*Region :* {}".format(str(job['region']))
    customMessage = customMessage + "\n*Timezone :* {}".format(str(job['timezone']))

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  # ----------------------------------------------------------------------------------------
  # Suspend Notification
  # ----------------------------------------------------------------------------------------
  elif(notificationAction == "suspendNotification"):
    customMessage = \
".\n\n\n\n\n------\n\
*Boru* :moon:\n\
------\n\n\
*{}* class: *{}* for *{}* is now Suspended. It will resume in the morning.\n\n\
<https://boruLink.com/viewJob/{}>\n".format(str(courseName), str(tag), str(instructor), str(_id))

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  # ----------------------------------------------------------------------------------------
  # Resume Notification
  # ----------------------------------------------------------------------------------------
  elif(notificationAction == "resumeNotification"):
    customMessage = \
".\n\n\n\n\n------\n\
*Boru* :sunny:\n\
------\n\n\
*{}* class: *{}* for *{}* is back up Running.\n\n\
<https://boruLink.com/viewJob/{}>\n".format(str(courseName), str(tag), str(instructor), str(_id))

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  # -------------------------------------------------------------------------------------
  # Finish Notification
  # -------------------------------------------------------------------------------------
  elif(notificationAction == "finishNotification"):
    customMessage = \
".\n\n\n\n\n------\n\
*Boru* :alien:\n\
------\n\n\
*{}* class: *{}* for *{}* is now finished.\n\n\
<https://boruLink.com/viewJob/{}>\n".format(str(courseName), str(tag), str(instructor), str(_id))

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  # -------------------------------------------------------------------------------------
  # Fail Notification
  # -------------------------------------------------------------------------------------
  elif(notificationAction == "failNotification"):
    customMessage = \
".\n\n\n\n\n------------\n\
:red_circle: *Boru* :space_invader: :space_invader: :space_invader:\n\
------------\n\n\
*{}* class: *{}* for *{}* has Failed to start!\n*Manual Intervention is required.*\n\n\
<https://boruLink.com/viewJob/{}>\n\n*Error Information:*\n".format(str(courseName), str(tag), str(instructor), str(_id))
    for i in errorInformation:
      customMessage = customMessage + \
"\n*{}*\n{}\n".format(i[0], i[1])

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  # -------------------------------------------------------------------------------------
  # Fail Suspend Notification
  # -------------------------------------------------------------------------------------
  elif(notificationAction == "failSuspendNotification"):
    customMessage = \
".\n\n\n\n\n------\n\
*Boru* :space_invader:\n\
------\n\n\
*{}* class: *{}* for *{}* has Failed to suspend. One or more Labs have failed to Suspend.\nThe 'jobStatus' of the class has been set to 'running'.\nThe 'suspendTime' has been removed from the list.\nThe job will continue suspending tomorrow if the class is still running. To stop the job from suspending, extend the finishDate of the job by 3 hours on the Boru website.\n\n\
<https://boruLink.com/viewJob/{}>\n\n*Error Information:*\n".format(str(courseName), str(tag), str(instructor), str(_id))
    for i in errorInformation:
      customMessage = customMessage + \
"\n*{}*\n{}\n".format(i[0], i[1])

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  # -------------------------------------------------------------------------------------
  # Fail Resume Notification
  # -------------------------------------------------------------------------------------
  elif(notificationAction == "failResumeNotification"):
    customMessage = \
".\n\n\n\n\n------\n\
*Boru* :space_invader:\n\
------\n\n\
*{}* class: *{}* for *{}* has Failed to resume. One or more Labs have failed to Resume.\nThe 'jobStatus' of the class has been set to 'running' in order for Boru to function normally!\nThe 'resumeTime' has been removed from the list.\n\n*IMPORTANT*: You need to resume the Labs manually.\n\n\
<https://boruLink.com/viewJob/{}>\n\n*Error Information:*\n".format(str(courseName), str(tag), str(instructor), str(_id))
    for i in errorInformation:
      customMessage = customMessage + \
"\n*{}*\n{}\n".format(i[0], i[1])

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  # -------------------------------------------------------------------------------------
  # Fail Finish Notification
  # -------------------------------------------------------------------------------------
  elif(notificationAction == "failFinishNotification"):
    customMessage = \
".\n\n\n\n\n------------\n\
*Boru* :space_invader:\n\
------------\n\n\
*{}* class: *{}* for *{}* has Failed to finish\n*Manual shutdown is required.*\n\n\
<https://boruLink.com/viewJob/{}>\n\n*Error Information:*\n".format(str(courseName), str(tag), str(instructor), str(_id))
    for i in errorInformation:
      customMessage = customMessage + \
"\n*{}*\n{}\n".format(i[0], i[1])

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  # -------------------------------------------------------------------------------------
  # Other
  # -------------------------------------------------------------------------------------
  else:
    customMessage = \
".\n\n\n\n\n------\n\
*Boru* :space_invader:\n\
------\n\n\
*{}* class: *{}* for *{}* has generated a *{}*.\n\n\
<https://boruLink.com/viewJob/{}>\n".format(str(courseName), str(tag), str(instructor), str(notificationAction), str(_id))

    # send message
    response = webhook(url, customMessage)
    log.info("[slackWebHook] " + response.text)

  return

def webhook(url, body):
  headers = {'Content-Type': 'application/json'}
  data_raw = {"text":body}
  data = json.dumps(data_raw)
  print (data)
  """ Create a session """
  s = requests.Session() # No need to close this
  response = s.post(url, headers=headers, data=data)
  return response
