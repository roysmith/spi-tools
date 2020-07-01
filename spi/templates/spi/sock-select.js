/* https://stackoverflow.com/questions/386281 */
$(document).ready(function() {
    $('#check-all').click(function(){
	$("input:checkbox").prop('checked', true);
    });
    $('#uncheck-all').click(function(){
	$("input:checkbox").prop('checked', false);
    });
});
