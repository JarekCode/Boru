<h2>Schedule</h2>
% import json

<div align="center">

<form method="post">
% jOutput = json.loads(output)

<form>

%# config.py setup

%import sys
%sys.path.insert(0, '/etc/boru/')
%import config

%# Getting 'namesOfCoursesHiddenByDefault' from config.py
%namesOfCoursesHiddenByDefault = config.getConfig("namesOfCoursesHiddenByDefault")

%# Getting 'instructorsWhoDoNotSeeHiddenCourses' from config.py
%instructorsWhoDoNotSeeHiddenCourses = config.getConfig("instructorsWhoDoNotSeeHiddenCourses")

%# The person logged-in is in variable: user['user']

<select name = "course" required>

% for doc in jOutput:

%if(user['user'] in instructorsWhoDoNotSeeHiddenCourses and doc['courseName'] in namesOfCoursesHiddenByDefault):
% pass
%else:
<option value="{{doc['courseName']}}"> {{doc['courseName']}}<br>
%end

% end
</select>
<br><input type="submit" value="Submit">

</form>

</div>

%rebase base

