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
sys.path.append('/etc/boru')
import config

def notify(recipient, job, message="Notification from Boru"):

  # ===================
  msg = MIMEMultipart()
  sendr = config.getConfig("awsSMTPSender")
  # =======================================

  # info for output file ================
  tag = str(job['tag'])
  courseName = str(job['courseName'])
  failedLabs = str(job['failedLabs'])
  errorInfo = str(job['errorInfo'])
  # =======================================

  # =================================================
  # Only send email when failedLabs actually exist
  # =================================================
  if(list(job['failedLabs'])):
    # ========================================================================
    msg['Subject'] = "{} : {} - Failed Labs".format(str(courseName), str(tag))
    body = "Here is a list of all labs that failed to start when starting the {}: {} class:\n".format(str(courseName), str(tag), str(failedLabs), str(errorInfo))
    
    for i in job['failedLabs']:
      body = body + "\n{}".format(str(i))

    body = body + "\n\nError Information:\n\n{}\n\n// Boru".format(str(errorInfo))

    msg['From'] = sendr
    
    if(isinstance(recipient, list)):
      msg['To'] = ", ".join(recipient)
    else:
      msg['To'] = recipient
    msg.attach(MIMEText(body))
    # ========================

    # send email ===================================================
    server = smtplib.SMTP('server.com', 587)
    server.starttls()
    awsSMTPuser = config.getConfig("awsSMTPuser")
    awsSMTPpassword = config.getConfig("awsSMTPpassword")
    server.login(awsSMTPuser, awsSMTPpassword)
    server.sendmail(sendr, recipient, msg.as_string())
    server.quit()
    # ===========
  else:
    return

