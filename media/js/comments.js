$(document).ready(function() {

    $("form.edit-comment input[name='cancel']").live('click', function() {
        var commentContainer = $(this).closest("div.comment-nonscore");
        commentContainer.children("form.edit-comment").addClass("hidden");
        commentContainer.children("div.hidden").children("blockquote.comment-body, ul.comment-links").unwrap();
        return false;
    });
    
    $("li.comment-action-confirmation-required > a").live('click', function() {
        var clickedAnchor = $(this);
        clickedAnchor.addClass("hidden");
        clickedAnchor.siblings("span.action-confirmation").removeClass("hidden");
        return false;
    });
    
    $("li.comment-action-confirmation-required > span.action-confirmation > a.no").live('click', function() {
        var activeSpan = $(this).parent();
        activeSpan.addClass("hidden");
        activeSpan.siblings("a.hidden").removeClass("hidden");
        return false;
    });
    
    $("li.delete-comment > span.action-confirmation > a.yes").live('click', function() {
        var clickedAnchor = $(this);
        $.post(clickedAnchor.attr("href"), function(comment_html) {
            clickedAnchor.closest("li.comment").html(comment_html);
        });
        return false;
    });
    
    $("li.edit-comment > a").live('click', function() {
        var clickedAnchor = $(this);
        var commentContainer = $(this).closest("div.comment-nonscore");
        var editForm = commentContainer.children("form.edit-comment");
        var commentBodyAndLinks = commentContainer.children("blockquote.comment-body, ul.comment-links");
        var editFormExists = editForm.length;
        if(editFormExists) {
            commentBodyAndLinks.wrapAll("<div class='hidden' />");
            editForm.removeClass("hidden");
        } else {
            $.get(clickedAnchor.attr("data-ajax-url"), function(edit_form_html) {
                commentBodyAndLinks.wrapAll("<div class='hidden' />");
                commentContainer.children("div.comment-header").after(edit_form_html);
            });
        }
        return false;
    });
    
    $("li.flag-comment > span.action-confirmation > a.yes").live('click', function() {
        var clickedAnchor = $(this);
        var parentSpan = $(this).parent();
        $.post(clickedAnchor.attr("href"), function() {
            parentSpan.addClass("hidden");
            parentSpan.siblings("span.action-performed").removeClass("hidden");
        });
        return false;
    });
    
    $("li.moderate-comment > span.action-confirmation > a.yes").live('click', function() {
        var clickedAnchor = $(this);
        $.post(clickedAnchor.attr("href"), function(comment_html) {
            clickedAnchor.closest("li.comment").html(comment_html);
        });
        return false;
    });
    
    $("li.reply-to-comment > a.close-comment-reply").live('click', function() {
        $("li.comment-reply-form").remove();
        
        var clickedLink = $(this);
        clickedLink.addClass("hidden");
        clickedLink.siblings("a.open-comment-reply").removeClass("hidden");
        
        return false;
    });
    
    $("li.reply-to-comment > a.open-comment-reply").live('click', function() {
        $("li.comment-reply-form").remove();
        $("a.close-comment-reply").addClass("hidden");
        $("a.open-comment-reply").removeClass("hidden");
        
        var clickedReplyLink = $(this);
        
        $.get(clickedReplyLink.attr("data-ajax-url"), function(reply_form_html) {
            clickedReplyLink.closest("li.comment").after(reply_form_html);
        });
        
        clickedReplyLink.addClass("hidden");
        clickedReplyLink.siblings("a.close-comment-reply").removeClass("hidden");
        
        return false;
    });
    
});
