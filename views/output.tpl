<h2>Output</h2>
% import json

<div align="left">
<button onclick="goBack()">Go Back</button>

<script>
function goBack() {
  window.history.back();
}
</script>

% for x in output:



{{x}} : {{output[x]}}<br/>

% end
</div>


%rebase base

