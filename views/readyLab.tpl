%import json



<div align="left">

<button onclick="goBack()">Go Back</button>

<script>
function goBack() {
  window.history.back();
}
</script>

% id = Output.get("_id")
% lab = Output.get("labName")

<p> The lab with the
% if id:
id:   {{ id }}
% elif lab:
name   "{{ lab }}" 
%end
is now marked as ready</p>
</div>

%rebase base
