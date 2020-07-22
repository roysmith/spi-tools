$(document).ready(function() {
    $('#id_case_name').select2({
	tags: true,
	placeholder: "Select (or enter) a SPI case",
	allowClear: true
    });
});
