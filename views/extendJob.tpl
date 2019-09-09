%import json



<div align="left">

<button onclick="goBack()">Go Back</button>

<script>
function goBack() {
  window.history.back();
}
</script>

% if (type(jobId) is str ):
%  jsonInput = json.loads(jobId)
%else:
%  jsonInput = jobId
%end

</p>Extended to {{ jsonInput['NewFinishTime'] }} </p>

<p><small>_id:   <a href = "/viewJob/{{ jsonInput['_id'] }}">{{ jsonInput['_id'] }}</small></p>
</div>

%rebase base
