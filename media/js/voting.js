$(document).ready(function() {
    
    $("div.comment-score > a").live('click', function(event) {
        var selectedAnchor = $(this);
        $.post(selectedAnchor.attr("href"), function(data) {
            var parent = selectedAnchor.parent();
            parent.load(parent.attr("data-ajax-url"), function() {
                parent.children("span.score-sum").text($.parseJSON(data).score.score);
            });
        });
        return false;
    });
    
});
