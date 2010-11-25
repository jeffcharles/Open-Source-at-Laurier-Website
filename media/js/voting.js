$(document).ready(function() {
    
    $("div.vote-box > a").live('click', function(event) {
        var selectedAnchor = $(this);
        var voteBox = $(selectedAnchor.parent());
        var voteBoxContainer = voteBox.parent();
        var scoreDiv = voteBoxContainer.find("div.score-sum");
        scoreDiv.html("<img src='/media/images/ajax-loader.gif' alt='Loading...' />");
        $.post(selectedAnchor.attr("href"), function(data) {
            voteBoxContainer.load(voteBox.attr("data-ajax-url"), function() {
                // need to repeat reference below b/c prev step nullifies reference to scoreDiv
                voteBoxContainer.find("div.score-sum").html($.parseJSON(data).score.score);
            });
        });
        return false;
    });
    
});
