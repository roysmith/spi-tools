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

    $('button.date-select').click(function(){
        $("input:checkbox").prop('checked', false);
        let found = false;
        for (button of $('#date-select-menu > button.dropdown-item')) {
            found = found || (button.dataset.date == this.dataset.date);
            if (found) {
                $(".spi-date-" + button.dataset.date + ">input:checkbox").prop('checked', true);
            };
        };
        this.blur();
    });
});
