/* Project specific Javascript goes here. */

(function($) {

    $(function() {
        $('.openInJOSM').click(function(e) {
            e.preventDefault();
            var link = $(this).attr('href');
            $.get(link)
                .done(function(response) {
                    //opened successfully, don't do anything
                })
                .fail(function(err) {
                    alert("Failed to open in JOSM. Is JOSM running and with remote control enabled?");
                });
        });
    });

})(jQuery);
