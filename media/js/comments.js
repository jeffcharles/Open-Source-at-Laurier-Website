$(document).ready(function() {
    
    $("li.moderate-comment > a").live('click', function() {
        var clickedAnchor = $(this);
        clickedAnchor.addClass("hidden");
        clickedAnchor.siblings("span.hidden").removeClass("hidden");
        return false;
    });
    
    $("li.moderate-comment > span > a.no").live('click', function() {
        var activeSpan = $(this).parent();
        activeSpan.addClass("hidden");
        activeSpan.siblings("a.hidden").removeClass("hidden");
        return false;
    });
    
    $("li.moderate-comment > span > a.yes").live('click', function() {
        var clickedAnchor = $(this);
        $.post(clickedAnchor.attr("href"), function(comment_html) {
            clickedAnchor.closest("li.comment").html(comment_html);
        });
        return false;
    })
    
});
