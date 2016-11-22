/* Project specific Javascript goes here. */

(function($) {

    $(function() {
        $('.openInJOSM').click(function(e) {
            e.preventDefault();
            var link = $(this).attr('href');
            if (location.protocol === 'https:') {
                link = link.replace('http', 'https');
                link = link.replace('8111', '8112');
            }
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
