$(document).ready(function() {
    
    $("div.vote-box > a").live('click', function(event) {
        var selectedAnchor = $(this);
        var voteBox = $(selectedAnchor.parent());
        var voteBoxContainer = voteBox.parent();
        $.post(selectedAnchor.attr("href"), function(data) {
            voteBoxContainer.load(voteBox.attr("data-ajax-url"), function() {
                voteBoxContainer.children("div.vote-box").children("span.score-sum").text($.parseJSON(data).score.score);
            });
        });
        return false;
    });
    
});
