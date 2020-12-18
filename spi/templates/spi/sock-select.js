/* https://stackoverflow.com/questions/386281 */
$(document).ready(function() {
    $('#check-all').click(function(){
	$("input:checkbox").prop('checked', true);
        this.blur();
    });
    $('#uncheck-all').click(function(){
	$("input:checkbox").prop('checked', false);
        this.blur();
    });
    $('.button-check-date').click(function(){
        $("td#spi-date-" + this.dataset.date + ">input:checkbox").prop('checked', true);
        this.blur();
    });
    $('.button-uncheck-date').click(function(){
        $("td#spi-date-" + this.dataset.date + ">input:checkbox").prop('checked', false);
        this.blur();
    });
});
