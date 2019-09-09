<h2>Error</h2>
% import json

<div align="left">
<button onclick="goBack()">Go Back</button>

<script>
function goBack() {
  window.history.back();
}
</script>
</div>

<p><b>{{ error }}</b></p>
%rebase base

