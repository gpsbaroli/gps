var $ = django.jQuery;
$(document).ready(function(){
	$('#calendarlink0').datepicker({
		changeMonth: true,
      changeYear: true,
      yearRange: "1900:2012",
      // You can put more options here.
	});
	alert($('#calendarlink0').val());
})