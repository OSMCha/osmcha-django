
(function($) {

    $(function() {
        $('.whitelist-user').on('click', function(e) {
            e.preventDefault();
            var name = $(this).attr('data-username');
            var confirmString = 'Are you sure you wish to white-list ' + name + '?';
            var url = '/whitelist-user';
            var data = {
                'name': name
            };
            var success = function(data) {
                alert('User successfully white-listed');
            };
            var error = function(data) {
                try {
                    alert(JSON.parse(data).error);
                } catch(err) {
                    alert("An unknown error occurred");
                }
            };
            if (confirm(confirmString)) {

                $.post(url, data)
                    .done(success)
                    .fail(error);
            };
        });
    });


})(jQuery);