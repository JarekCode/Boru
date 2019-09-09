#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Jaroslaw Glodowski

# https://realpython.com/python-send-email/#including-html-content

# There are 8 possible notificationActions:
  #  1. runningNotification - Sent after ALL labs are up. The jobStatus is set to running. DONE
  #  2. suspendNotification - Sent after ALL labs are suspended. The jobStatus is set to suspended. DONE
  #  3. resumeNotification - Sent after  ALL labs are resumed. The jobStatus is set back to running. DONE
  #  4. finishNotification - Sent after ALL labs are finished. The jobStatus is set to finished. DONE
  #  5. failNotification - Sent after the limit of failures is reached when job tried to start. The jobStatus is set to failed. DONE
  #  6. failSuspendNotification - Sent after ONE lab fails to suspend. DONE
  #  7. failResumeNotification - Sent after ONE lab fails to resume. DONE
  #  8. failFinishNotification - Sent after ONE lab fails to finish.

# Import config.py
import sys
sys.path.insert(0, '/etc/boru/')
sys.path.append("/var/www/html/sshkeys")
import config

# Import email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import other
from pytz import timezone
import json, datetime

def notify(recipient, job, message="Notification from Boru"):
  # EmailMessage
  msg = MIMEMultipart("alternative")
  # =========================================================================================================
  # Keys retunred from the cloudFormation output that will be ignored in the email where specified
  whiteListOutputKeys = ["AWSAccount", "UserName"]
  # converting times to user local timezone
  userTimezone = str(job['timezone'])
  # startDate / Converted
  startDate = job['startDate']
  startDate = convertTimeFromUTC(startDate, userTimezone)
  startDate = startDate.replace(tzinfo = None)
  # finishDate / Converted
  finishDate = job['finishDate']
  finishDate = convertTimeFromUTC(finishDate, userTimezone)
  finishDate = finishDate.replace(tzinfo = None)
  # listOfSuspendTimes / Not-Converted
  listOfSuspendTimes = job['listOfSuspendTimes']
  # listOfResumeTimes / Not-Converted
  listOfResumeTimes = job['listOfResumeTimes']
  # list of labs for attachment with ssh keys
  listOfLabs = job['labs']
  # Getting the instructorInfo for "Hello <instructor_name>,"
  instructorInfo = config.getConfig("instructorInfo")
  for i in instructorInfo:
    if(str(i['username']) == str(job['instructor'])):
      instructorFullName = str(i['fullName'])
  # =========================================================================================================

  # ===================
  # runningNotification
  # ===================
  if(message == "runningNotification"):
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " is now " + str(job['jobStatus']))
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> in now ready.<br>
      Please find all the information about your class below:
    </p>
    <p>
      <strong>Account Information</strong><br>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), subtype='html')
    for i in job['successInfo']:
      body = body + '''\
      <br><strong>Account & Username:</strong> {}
      '''.format(str(i[0]).lower(), subtype='html')
      for j in i[1]:
        if(str(j['OutputKey']) not in whiteListOutputKeys):
          body = body + '''
      <br><strong>{}:</strong> {}
          '''.format(str(j['OutputKey']), str(j['OutputValue']), subtype='html')
      body = body + "<br>"
    body = body + '''
      <br><strong>Instructor:</strong> {}
    '''.format(str(instructorFullName), subtype='html')
    body = body + '''
      <br><strong>Region:</strong> {}
    '''.format(str(job['region']), subtype='html')
    body = body + '''
      <br><strong>Timezone:</strong> {}
    '''.format(str(job['timezone']), subtype='html')
    body = body + '''
      <br><br><strong>Class start date:</strong> {}
    '''.format(str(startDate), subtype='html')
    body = body + '''
      <br><strong>Class finish date:</strong> {}
    '''.format(str(finishDate), subtype='html')
    # Send only when suspend == 'yes' in job -----------------------
    if(str(job['suspend']) == str("yes")):
      body = body + '''
      <br><br><strong>Class suspend times</strong><br>
      '''
      # suspend dates
      for i in listOfSuspendTimes:
        # convert time
        i = convertTimeFromUTC(i, userTimezone)
        i = i.replace(tzinfo = None)
        # print time
        body = body + "<br>    {}".format(str(i))
      # resume dates
      body = body + '''
      <br><br><strong>Class resume times</strong><br>
      '''
      for i in listOfResumeTimes:
        # convert time
        i = convertTimeFromUTC(i, userTimezone)
        i = i.replace(tzinfo = None)
        # print time
        body = body + "<br>    {}".format(str(i))
    # --------------------------------------------------------------
    body = body + '''
    </p>
    <p>
      <br><strong>Support</strong>
    </p>
    <p>
      If you have any issues, please reply to: USM-Anywhere-Training@alienvault.com
    </p>
    <p>
      // Boru
    </p>
  </body>
</html>
    '''.format(str(job['_id']))

    # attachment ==================
    for i in listOfLabs:
      infoFile = ""
      f = open("/var/www/html/sshkeys/{}.pem".format(i))
      infoFile = infoFile + f.read()
      # Don't forget
      f.close()
      attachment = MIMEText(infoFile)
      attachment.add_header('Content-Disposition', 'attachment', filename="{}.pem".format(i))
      msg.attach(attachment)
    # ======================

  # ===================
  # suspendNotification
  # ===================
  elif(message == "suspendNotification"):
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " is now " + str(job['jobStatus']))
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> in now suspended overnight.<br>
      The class will resume in the morning.
    </p>
    <p>
      // Boru
    </p>
  </body>
</html>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), subtype='html')

  # ==================
  # resumeNotification
  # ==================
  elif(message == "resumeNotification"):
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " is now " + str(job['jobStatus']))
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> has resumed.<br>
    </p>
    <p>
      // Boru
    </p>
  </body>
</html>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), subtype='html')

  # ==================
  # finishNotification
  # ==================
  elif(message == "finishNotification"):
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " is now " + str(job['jobStatus']))
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> is now finished.<br>
    </p>
    <p>
      // Boru
    </p>
  </body>
</html>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), subtype='html')

  # ================
  # failNotification
  # ================
  elif(message == "failNotification"):
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " " + str(job['jobStatus']).upper() + " to deploy")
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> failed to deploy.<br>
      Manual intervention is required by an administrator to create a new class for you.<br>
      <br>
      Please contact USM-Anywhere-Training@alienvault.com to resolve this problem.<br>
      <br>
      Error information can be found below and <a href="https://boruLink.com/viewJob/{}">here</a> and also in my logs.
    </p>
    <p>
      <strong>Error Information</strong>
    </p>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), str(job['_id']), subtype='html')
    for i in job['errorInfo']:
      body = body + '''\
    <p>
      <strong>{}</strong><br>{}<br><br>
    </p>
    '''.format(str(i[0]), str(i[1]))
    body = body + '''\
    <p>
      // Boru
    </p>
  </body>
</html>
    '''

  # =======================
  # failSuspendNotification
  # =======================
  elif(message == "failSuspendNotification"):
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " FAILED to suspend")
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> failed to suspend.<br>
      One or more labs failed to suspend overnight. (Please ignore if this email was sent multiple times)<br>
      No manual intervention is required.<br>
      Up to date information about your class can be found <a href="https://boruLink.com/viewJob/{}">here</a>.<br>
      <br>
      I have set the job status to <strong>running</strong> in order to maintain your class.<br>
      You can stop the class from suspending by <strong>extending the finish date</strong> <a href="https://boruLink.com/viewJob/{}">here</a>.<br>
      <br>
      Error information can be found <a href="https://boruLink.com/viewJob/{}">here</a> and in my logs.
    </p>
    <p>
      // Boru
    </p>
  </body>
</html>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), str(job['_id']), str(job['_id']), str(job['_id']), subtype='html')

  # =======================
  # failResumeNotification
  # =======================
  elif(message == "failResumeNotification"):
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " FAILED to resume")
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> failed to resume.<br>
      One or more labs failed to resume this morning. (Please ignore if this email was sent multiple times)<br>
      Manual intervention is required.<br>
      Some students will need to manually start their instances today.<br>
      <br>
      I have set the job status to <strong>running</strong> in order to maintain your class. Some instances may be still suspended.<br>
      You can stop the class from suspending by <strong>extending the finish date</strong> <a href="https://boruLink.com/viewJob/{}">here</a>.<br>
      <br>
      Error information can be found <a href="https://boruLink.com/viewJob/{}">here</a> and in my logs.
    </p>
    <p>
      // Boru
    </p>
  </body>
</html>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), str(job['_id']), str(job['_id']), subtype='html')

  # =======================
  # failFinishNotification
  # =======================
  elif(message == "failFinishNotification"):
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " FAILED to finish")
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> failed to finish.<br>
      One or more labs failed to finish in the time scheduled.<br>
      Manual intervention is required.<br>
      <br>
      The job status is set to <strong>FailedToFinish</strong> as the class did not finish properly. Some instances may be still running.<br>
      You can finish the class again manually <a href="https://boruLink.com/viewJob/{}">here</a>.<br>
      <br>
      Error information can be found <a href="https://boruLink.com/viewJob/{}">here</a> and in my logs.
    </p>
    <p>
      // Boru
    </p>
  </body>
</html>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), str(job['_id']), str(job['_id']), str(job['_id']), subtype='html')

  # ==========================
  # Other Unknown Notification
  # ==========================
  else:
    # Subject
    msg['Subject'] = (str(job['courseName']) + " : " + str(job['tag']) + " has sent " + str(message))
    body = '''\
<html>
  <head></head>
  <body>
    <p>
      Hello {},
    </p>
    <p>
      Your <strong>{}</strong> class: <strong>{}</strong> has sent <strong>{}</strong> Notification.<br>
      <br>
      Information about your class can be found <a href="https://boruLink.com/viewJob/{}">here</a>.<br>
    </p>
    <p>
      // Boru
    </p>
  </body>
</html>
    '''.format(str(instructorFullName), str(job['courseName']), str(job['tag']), str(message), str(job['_id']), str(job['_id']), str(job['_id']), subtype='html')

  # Sender
  configSender = config.getConfig("awsSMTPSender")
  msg['From'] = configSender

  # Recipient
  if(isinstance(recipient, list)):
    msg['To'] = ", ".join(recipient)
  else:
    msg['To'] = recipient

  # Send the Email
  html = MIMEText(body, "html")
  msg.attach(html)
  server = smtplib.SMTP('server.com', 587)
  server.starttls()
  awsSMTPuser = config.getConfig("awsSMTPuser")
  awsSMTPpassword = config.getConfig("awsSMTPpassword")
  server.login(str(awsSMTPuser), str(awsSMTPpassword))
  server.sendmail(configSender, recipient, msg.as_string())
  server.quit()

  # Return
  return {"Info:":"Complete"}

def convertTimeFromUTC(userTime, userTimezone):
  tz = timezone("UTC")
  return tz.normalize(tz.localize(userTime)).astimezone(timezone(userTimezone))

