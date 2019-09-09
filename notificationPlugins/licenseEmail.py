#!/usr/bin/env python

import smtplib
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import json, datetime
from pytz import timezone
from bson import ObjectId
# This is needed to import the boru python csuspendNotificationonfig file
import sys

# path for output file ===============
sys.path.append("../boru/licenseInfo")
# ====================================

sys.path.append('/etc/boru')
import config

def notify(recipient, job, message="Notification from Boru"):

  # ===================
  msg = MIMEMultipart()
  sendr = config.getConfig("awsSMTPSender")
  # =======================================

  # info for output file ================
  tag = str(job['tag'])
  startDate = str(job['startDate'])
  startDate = startDate.replace(" ", "-")
  # =====================================

  # ========================================
  msg['Subject'] = "{}-{} licenses are ready".format(str(tag), str(startDate))
  body = "Your licenses are ready.\nPlease find them attached below.\n\n// Boru"

  msg['From'] = sendr
  if(isinstance(recipient, list)):
    msg['To'] = ", ".join(recipient)
  else:
    msg['To'] = recipient

  msg.attach(MIMEText(body))
  # ========================

  # attachment ==================
  filename = "{}-{}-licenses.txt".format(str(tag), str(startDate))
  f = open("../licenseInfo/{}-{}-licenses.txt".format(str(tag), str(startDate)))
  attachment = MIMEText(f.read())
  attachment.add_header('Content-Disposition', 'attachment', filename=filename)
  msg.attach(attachment)
  # Don't forget
  f.close()
  # =======

  # send email ===================================================
  server = smtplib.SMTP('server.com', 587)
  server.starttls()
  awsSMTPuser = config.getConfig("awsSMTPuser")
  awsSMTPpassword = config.getConfig("awsSMTPpassword")
  server.login(awsSMTPuser, awsSMTPpassword)
  server.sendmail(sendr, recipient, msg.as_string())
  server.quit()
  # ===========

'''
# Testing
job = {'failedAttempts': 0, 'tag': 'licenseTest1', 'notifications': [{'notificationKey': 'sendLicensesToEmail', 'recipients': 'jglodowski@alienvault.com', 'validInput': 'N/A', 'notificationType': 'prompt', 'notificationFile': 'licenseEmail', 'notificationAction': 'runningNotification'}], 'suspendedLabs': [], 'failedLabs': [], 'suspend': 'yes', 'sendLicensesToEmail': 'jglodowski@alienvault.com', 'environment': 'av', 'sender': 'jglodowski', 'finishDate': datetime.datetime(2019, 6, 21, 18, 0), 'sensor': 'yes', 'keys': 'someKey1 someKey2 someKey3', 'suspendScriptName': 'dummyScript', 'labs': ['license01'], 'startScriptName': 'createLicense', 'listOfResumeTimes': [], 'errorInfo': [], 'courseTemplate': 'N/A', 'numberOfLabs': 1, 'timezone': 'Europe/Dublin', 'sensorTemplate': 'N/A', 'finishScriptName': 'dummyScript', 'instructor': 'jglodowski', 'finishedLabs': [], 'resumeScriptName': 'dummyScript', 'successInfo': [[]], 'courseName': 'license', 'startDate': datetime.datetime(2019, 6, 21, 12, 13), 'course': 'license', 'listOfSuspendTimes': [], 'jobStatus': 'running', '_id': '5d0cc9c4c8ce8766a26c362b', 'region': 'license'}
notify("jglodowski@alienvault.com", job, "N/A")
'''

