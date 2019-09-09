This does not create the labs in your environment. This adds entries to the database only. 
<form action="/addLabs" method="post">
<table>
<tr><td>Lab Name:</td><td><input type="text" name="labName"></td></tr>
<tr><td>Range From:</td><td><input type="text" name="rangeFrom"></td></tr>
<tr><td>Range To:</td><td><input type="text" name="rangeTo"></td></tr>
<tr><td>Environment:</td><td><input type="text" name="environment"></td></tr>
</table>
<input type="submit" value="Add">
</form>
%rebase base

