/*
 * Initialize tooltips.  See https://getbootstrap.com/docs/4.0/components/tooltips
 */
$(function () {
    $('[data-bs-toggle="tooltip"]').tooltip()
})

$(document).ready(function() {
    $('#tag-card').on('shown.bs.collapse hidden.bs.collapse', function() {
        $(':button[data-bs-target="#tag-card"]').blur();
    });
});
