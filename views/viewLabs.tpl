<html>
<script> 
   function clickAndDisable(link) {
     // disable subsequent clicks
     link.onclick = function(event) {
        event.preventDefault();
     }
   }   
</script>

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
  
%import json
%try:
%    user = request.auth[0]
%  except:
%    user = ""
{{user}}

<!-- View Running Labs -->
  <div class="w3-container" id="services" style="margin-top:75px">
    <h1 class="w3-xxxlarge w3-text-red">Running</h1>

%for doc in dbOutput:                   # for jsonOutput 1
% if doc['status'] != 'running':
%  continue
% end
% heading = doc['labName']
% dbId = doc['_id']
% jobEnvironment = doc['environment']
% jobID = doc['jobID']


<button class="collapsible">{{heading}}</button>
<div class="content" align="left">

<table>
%  for k, v in sorted(doc.items()):              # for doc 2
%    if (k == "jobID"):                         # if k 3
      <tr><td>{{k}}</td> <td><a href="/viewJob/{{v}}">{{v}}</a></td><td></td><td></td></tr>
%   elif (k == "_id"):
      <tr><td>{{k}}</td> <td><a href="/viewLab/_id/{{v}}">{{v}}</a></td><td></td><td></td></tr>
%   elif (k == "labName"):
      <tr><td>{{k}}</td> <td><a href="/viewLab/labName/{{v}}">{{v}}</a></td><td></td><td></td></tr>
%   else:
      <tr><td>{{k}}</td> <td>{{v}}</td><td></td><td></td></tr>
%    end                                     #if k end 3
%  end                                   # end for doc 2
</table>
<tr>
<td><a class = "customButton" href = "/cleanLab/{{heading}}/{{jobEnvironment}}">Manual Lab clean-up</a></td>
<td><a class = "customButton" href = "/createAdmin/{{heading}}/{{jobEnvironment}}" onclick="clickAndDisable(this);">Create Admin User</a></td>
<td><a class = "customButton" href = "/removeAdmin/{{heading}}/{{jobEnvironment}}" onclick="clickAndDisable(this);">Remove Admin User</a></td>
<td><a class = "customButton" href = "/quarantineLab/{{heading}}/{{jobID}}" onclick="clickAndDisable(this);">Quarantine Lab</a></td>
</tr>
</div>
<p>&nbsp;</p>
% end                                   # end for dbOutput 1
    </p>
  </div>


<!-- View Failed Labs -->
  <div class="w3-container" id="services" style="margin-top:75px">
    <h1 class="w3-xxxlarge w3-text-red">Failed</h1>

%for doc in dbOutput:                   # for jsonOutput 1
% if doc['status'] != 'failed':
%  continue
% end
% heading = doc['labName']
% dbId = doc['_id']
% jobEnvironment = doc['environment']
% jobID = doc['jobID']

<button class="collapsible">{{heading}}</button>
<div class="content" align="left">

<table>
%  for k, v in sorted(doc.items()):              # for doc 2
%    if (k == "jobID"):                         # if k 3
      <tr><td>{{k}}</td> <td><a href="/viewJob/{{v}}">{{v}}<br/></a></td><td></td><td></td></tr>
%   elif (k == "_id"):
      <tr><td>{{k}}</td> <td><a href="/viewLab/_id/{{v}}">{{v}}<br/></a></td><td></td><td></td></tr>
%   elif (k == "labName"):
      <tr><td>{{k}}</td> <td><a href="/viewLab/labName/{{v}}">{{v}}<br/></a></td><td></td><td></td></tr>
%    else:
       <tr><td>{{k}}</td> <td>{{v}}<br/></td><td></td><td></td></tr>
%    end                                     #if k end 3
%  end                                   # end for doc 2
</table>
<tr>
<td><a class = "customButton" href = "/readyLab/labName/{{heading}}">Mark as Free</a></td>
<td><a class = "customButton" href = "/cleanLab/{{heading}}/{{jobEnvironment}}">Manual Lab clean-up</a></td>
<td><a class = "customButton" href = "/createAdmin/{{heading}}/{{jobEnvironment}}" onclick="clickAndDisable(this);">Create Admin User</a></td>
<td><a class = "customButton" href = "/removeAdmin/{{heading}}/{{jobEnvironment}}" onclick="clickAndDisable(this);">Remove Admin User</a></td>
<td><a class = "customButton" href = "/quarantineLab/{{heading}}/{{jobID}}" onclick="clickAndDisable(this);">Quarantine Lab</a></td>
</tr>
</div>
<p>&nbsp;</p>
% end                                   # end for dbOutput 1
    </p>
  </div>

<!-- View Free Labs -->
  <div class="w3-container" id="services" style="margin-top:75px">
    <h1 class="w3-xxxlarge w3-text-red">Free</h1>

%for doc in dbOutput:                   # for jsonOutput 1
% if doc['status'] != 'free':
%  continue
% end
% heading = doc['labName']
% dbId = doc['_id']
% jobEnvironment = doc['environment']

<button class="collapsible">{{heading}}</button>
<div class="content" align="left">
<table>
%  for k, v in sorted(doc.items()):              # for doc 2
%    if (k == "jobID"):                         # if k 3
      <tr><td>{{k}}</td> <td><a href="../viewJob/{{v}}">{{v}}<br/></a></td><td></td></tr>
%   elif (k == "_id"):
      <tr><td>{{k}}</td> <td><a href="/viewLab/_id/{{v}}">{{v}}<br/></a></td><td></td></tr>
%   elif (k == "labName"):
      <tr><td>{{k}}</td> <td><a href="/viewLab/labName/{{v}}">{{v}}<br/></a></td><td></td></tr>
%    else:
       <tr><td>{{k}}</td> <td>{{v}}<br/></td><td></td></tr>
%    end                                     #if k end 3
%  end                                   # end for doc 2
</table>
<tr>
<td><a class = "customButton" href = "/cleanLab/{{heading}}/{{jobEnvironment}}">Manual Lab clean-up</a></td>
<td><a class = "customButton" href = "/createAdmin/{{heading}}/{{jobEnvironment}}" onclick="clickAndDisable(this);">Create Admin User</a></td>
<td><a class = "customButton" href = "/removeAdmin/{{heading}}/{{jobEnvironment}}" onclick="clickAndDisable(this);">Remove Admin User</a></td>
</tr>
</div>
<p>&nbsp;</p>
% end                                   # end for dbOutput 1
    </p>
  </div>

<!-- View Other Labs -->
  <div class="w3-container" id="services" style="margin-top:75px">
    <h1 class="w3-xxxlarge w3-text-red">Other</h1>

%for doc in dbOutput:                   # for jsonOutput 1
% if (doc['status'] == 'free') or (doc['status'] == 'running') or (doc['status'] == 'failed'):
%  continue
% end
% heading = doc['labName']
% dbId = doc['_id']
% jobEnvironment = doc['environment']
% jobID = doc['jobID']

<button class="collapsible">{{heading}}</button>
<div class="content" align="left">
<table>
%  for k, v in sorted(doc.items()):              # for doc 2
%    if (k == "jobID"):                         # if k 3
      <tr><td>{{k}}</td> <td><a href="../viewJob/{{v}}">{{v}}<br/></a></td><td></td><td></td><td></td></tr>
%   elif (k == "_id"):
      <tr><td>{{k}}</td> <td><a href="/viewLab/_id/{{v}}">{{v}}<br/></a></td><td></td><td></td><td></td></tr>
%   elif (k == "labName"):
      <tr><td>{{k}}</td> <td><a href="/viewLab/labName/{{v}}">{{v}}<br/></a></td><td></td><td></td><td></td></tr>
%    else:
       <tr><td>{{k}}</td> <td>{{v}}<br/></td><td></td><td></td><td></td></tr>
%    end                                     #if k end 3
%  end                                   # end for doc 2
</table>
<tr>
<td><a class = "customButton" href = "/cleanLab/{{heading}}/{{jobEnvironment}}">Manual Lab clean-up</a></td>
<td><a class = "customButton" href = "/createAdmin/{{heading}}/{{jobEnvironment}}" onclick="clickAndDisable(this);">Create Admin User</a></td>
<td><a class = "customButton" href = "/removeAdmin/{{heading}}/{{jobEnvironment}}" onclick="clickAndDisable(this);">Remove Admin User</a></td>
<td><a class = "customButton" href = "/quarantineLab/{{heading}}/{{jobID}}" onclick="clickAndDisable(this);">Quarantine Lab</a></td>
<td><a class = "customButton" href = "/readyLab/labName/{{heading}}">Mark as Free</a><br/>
</tr>
</div>
<p>&nbsp;</p>
% end                                   # end for dbOutput 1
    </p>
  </div>

<a class = "customButton" href = "/addLabs">Add Lab</a></br>

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
