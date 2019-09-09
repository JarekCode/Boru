<html>
<head><style>
.collapsible {
  background-color: #777;
  color: white;
  cursor: pointer;
  width: 100%;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;
}

.active, .collapsible:hover {
  background-color: #555;
}

.content {
  display: none;
  overflow: hidden;
}
</style></head>

<body>
  
  
  <!-- View Jobs -->
  <div class="w3-container" id="services" style="margin-top:75px">
    <h1 class="w3-xxxlarge w3-text-red"><b>View {{pageName}}</b></h1>

%summary = False
%if pageName != "Job":
% summary = True
%end


%import json
% # Cycle through the json file as in comes in as a list
%for doc in dbOutput:                   # for jsonOutput 1
% heading = ((doc['startDate'])[:-9] + " | " + doc['course'] + " | " + doc['instructor'] + " | " + doc['tag'] + " | " + doc['jobStatus'])
% jobId = doc['_id']

%if summary:
<button class="collapsible">{{heading}}</button>
<div class="content">
%else:
<h2>{{heading}}</h2>
%end
<table>
%  for k, v in sorted(doc.items()):              # for doc 2
% delete = False

% # Only show the delete link for jobs that are pending, failed or finished
% if (doc['jobStatus'] == "pending") or (doc['jobStatus'] == "failed") or (doc['jobStatus'] == "finished"):
%   delete = True
% end

% # If the key is _id then add a link to the job page for that ID
%    if (k == "_id"):      # if k 3
      <tr><td>{{k}}</td><td><a href="../viewJob/{{jobId}}">{{v}}</b></a></td></tr>
%
% # If the key is labs then add a link to the lab page
%    elif (k == "labs"):
<tr><td>{{k}}</td><td>
% for org in doc[k]:
 <a href="../viewLab/labName/{{org}}"><b>{{org}}</b></a>
% end
</td>
</tr>

%    elif (k == "errorInfo") and not summary:
<tr><td>{{k}}</td><td>
% for error in doc[k]:
 <strong>{{error[0]}}</strong></br>{{error[1]}}</br></br>
% end
</td>
</tr>

%    elif (k == "successInfo") and not summary:
<tr><td>{{k}}</td><td>
% for i in doc[k]:
% accountNameLowerCase = str(i[0]).lower()
 <strong>Account:</strong> {{accountNameLowerCase}}</br>
% for j in i[1]:
 <strong>{{j['OutputKey']}}:</strong> {{j['OutputValue']}}</br>
% end
</br>
% end
</td>
</tr>

%    elif (k == "notifications") and not summary:
<tr><td>{{k}}</td><td>
% for notification in doc[k]:
 <strong>Notification Key:</strong> {{notification['notificationKey']}}</br><strong>Notification Type:</strong> {{notification['notificationType']}}</br><strong>Notification File:</strong> {{notification['notificationFile']}}</br><strong>Recipients:</strong> {{notification['recipients']}}</br></br>
% end
</td>
</tr>

% # If the key is FailedLabs then add a link to the lab page
%    elif (k == "failedLabs"):
<tr><td>{{k}}</td><td>
% for org in doc[k]:
 <a href="../viewLab/labName/{{org}}"><b>{{org}}</b></a>
% end
</td>
</tr>



% # If the key is finished Date then add an option to extend the labs
%   elif (k == "finishDate") and not summary:
% # Do not allow job extend when the job is finishing
%     if (doc['jobStatus'] == "finishing"):
       <tr><td>{{k}}</td><td>{{v}} UTC </td></tr>
%     else:
       <tr><td>{{k}}</td><td>{{v}} UTC <a href="/extendJob/{{jobId}}" title="Time in UTC | This will disable the suspending of labs">Extend by 3 hours</a></td></tr>
%     end
%    elif summary and (k not in ['sender', 'instructor', 'region', 'startDate', 'finishDate', 'timezone', 'numberOfLabs']):
%      pass
%    else:
%      if (k in ['startDate', 'finishDate']):
%        #v = v[:-9] This will hide the hour/min/sec
%        v = v + " UTC"
%      end
       <tr><td>{{k}}</td><td>{{v}}</td></tr>

%    end                                     #if k end 3

%  end                                   # end for doc 2
</table>
% # If the variable delete is true this indicates that this job can be deleted.
% # Do not allow job extend when the job is finishing
%     if (doc['jobStatus'] == "finishing"):
%       pass
%     else:
% if delete and not summary:
   <a class = "customButton" href="../deleteJob/{{jobId}}" style="color: rgb(255,0,0)">Delete</a>
% elif not summary:
   <a class = "customButton" href="../stopJob/{{jobId}}" style="color: rgb(255,0,0)">Finish Running Job</a>
% end
% end

</div>
<p>&nbsp;</p>
% end                                   # end for dbOutput 1
    </p>
  </div>


<!-- Script for collapsing the entries -->
<script>
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}
</script>

</body>
</html>

%rebase base
