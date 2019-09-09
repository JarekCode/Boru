#!/usr/bin/env python

# """
# joriordan@alienvault.com
# Script to send an email
# http://naelshiab.com/tutorial-send-email-python/
# """
import smtplib
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import json, datetime
from pytz import timezone
from bson import ObjectId
import pymongo, datetime
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


  # ========================================
  msg['Subject'] = "Weekly Labs Status Report"
  body = getLabStatus()

  print(body)
  return
  msg['From'] = sendr
  if(isinstance(recipient, list)):
    msg['To'] = ", ".join(recipient)
  else:
    msg['To'] = recipient

  msg.attach(MIMEText(body))
  # ========================

  # send email ===================================================
  server = smtplib.SMTP('email-smtp.us-east-1.amazonaws.com', 587)
  server.starttls()
  awsSMTPuser = config.getConfig("awsSMTPuser")
  awsSMTPpassword = config.getConfig("awsSMTPpassword")
  server.login(awsSMTPuser, awsSMTPpassword)
  server.sendmail(sendr, recipient, msg.as_string())
  server.quit()
  # ===========
  print("Done.")

def getLabStatus():
  # MongoDB
  mongoClient = pymongo.MongoClient()
  mongodb = mongoClient.boruDB
  # lists of labs
  failedLabs = []
  otherLabs = []
  runningLabs = []
  freeLabs = []
  # current time
  currentTime = datetime.datetime.utcnow()
  # getting all labs
  labs = mongodb.labs.find()
  # sorting all labs into lists
  for i in labs:
    if((i['status'] == "failed") or (i['status'] == "failedToFinish")):
      failedLabs.append(i)
    elif(i['status'] == "running"):
      runningLabs.append(i)
    elif(i['status'] == "free"):
      freeLabs.append(i)
    else:
      otherLabs.append(i)
  # report info
  report = ("\n====================================")
  report = report + ("\nBoru Database: Labs Status Report\nDate UTC: {}".format(currentTime))
  report = report + ("\n====================================")
  report = report + ("\nFAILED:\n")
  for i in failedLabs:
    report = report + (str(i) + "\n")
  report = report + ("\nOTHER:\n")
  for i in otherLabs:
    report = report + (str(i) + "\n")
  report = report + ("\nRUNNING:\n")
  for i in runningLabs:
    report = report + (str(i) + "\n")
  report = report + ("\nFREE:\n")
  for i in freeLabs:
    report = report + (str(i) + "\n")
  # close MongoDB
  mongoClient.close()
  return report

notify("jglodowski@alienvault.com", "N/A", message="Notification from Boru")