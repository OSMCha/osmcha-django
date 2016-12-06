$(function() {
    var id = CHANGESET_ID; // defined in changeset_detail template
    var url = 'https://osm-comments-api.mapbox.com/api/v1/changesets/' + id;
    var $xhr = $.get(url);
    var tmpl = jsrender.templates($('#discussionsTpl').html());

    $xhr.success(function(data) {
        var html = tmpl.render({
            'comments': data.properties.comments,
            'count': data.properties.comments.length 
        });
        $('#changesetDiscussions').html(html);
    });
    $xhr.fail(function(err) {
        if (err.status === 404) {
            var html = tmpl.render({'comments': null});
            $('#changesetDiscussions').html(html);
        }
    });
});