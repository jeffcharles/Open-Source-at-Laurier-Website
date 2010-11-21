$(document).ready(function() {

    (function() {
        if($("div.comment-pagination").children("a[rel='next']").length > 0) {
            $("li.load-more-comments").removeClass("hidden");
            $("div.comment-pagination").remove();
        }
    })();
    
    $("li.load-more-comments > a").live('click', function() {
        var loadMoreElement = $(this).parent();
        $.get($(this).attr("href"), function(commentListHtml) {
            loadMoreElement.after(commentListHtml);
            loadMoreElement.remove();
            $("li.load-more-comments").removeClass("hidden");
        });
        return false;
    });

    $("form.edit-comment input[name='cancel']").live('click', function() {
        var commentContainer = $(this).closest("div.comment-nonscore");
        commentContainer.children("form.edit-comment").addClass("hidden");
        commentContainer.children("div.hidden").children("blockquote.comment-body, ul.comment-links").unwrap();
        return false;
    });
    
    $("form.edit-comment input[name='post']").live('click', function() {
        var editForm = $(this).closest("form.edit-comment");
        $.post(editForm.attr("action"), editForm.serialize(), function(commentHtml) {
            editForm.closest("li.comment").html(commentHtml);
        });
        return false;
    });
    
    $("form.post-comment input[name='cancel']").live('click', function() {
        var replyLi = $(this).closest("li.comment-reply-form");
        replyLi.addClass("hidden");
        
        var parentLi = replyLi.prev();
        parentLi.find("a.close-comment-reply").addClass("hidden");
        parentLi.find("a.open-comment-reply").removeClass("hidden");
        
        return false;
    });
    
    $("form.post-comment input[name='post']").live('click', function() {
        var isReplyForm = $(this).closest("li.comment-reply-form").length > 0;
        var commentForm = $(this).closest("form");
        
        $.post(commentForm.attr("action"), commentForm.serialize(), function(commentHtml) {
            var commentPlacementDelegates = {
            
                replyAndNewest: function(commentHtml, commentWrapper, commentReplyFormLi) {
                    var loadMoreIsNextElement = commentReplyFormLi.next("li.load-more-comments:not(:hidden)").length > 0;
                    if(!loadMoreIsNextElement) {
                        $(commentHtml).insertAfter(commentReplyFormLi).wrapAll(commentWrapper);
                        return;
                    }
                    showCommentPostedMessage();
                },
                
                postAndNewest: function(commentHtml, commentWrapper) {
                    $(commentHtml).insertBefore("li.comment:first").wrapAll(commentWrapper);
                },
                
                replyAndOldest: function(commentHtml, commentWrapper, showCommentPostedMessage, commentReplyFormLi, loadMorePresentInThread, commentHasChildren) {
                
                    if(!loadMorePresentInThread()) {
                        if(commentHasChildren) {
                            $(commentHtml).insertAfter(commentReplyFormLi.nextUntil("li.comment:not(.comment-child)").last()).wrapAll(commentWrapper);
                            return;
                        }
                        $(commentHtml).insertAfter(commentReplyFormLi).wrapAll(commentWrapper);
                        return;
                    }
                    showCommentPostedMessage();
                },
                
                postAndOldest: function(commentHtml, commentWrapper, showCommentPostedMessage) {
                    var loadMorePresent = $("li.load-more-comments:not('.hidden')").length > 0;
                    if(!loadMorePresent) {
                        $(commentHtml).insertAfter("li.comment:last").wrapAll(commentWrapper);
                        return;
                    }
                    showCommentPostedMessage();
                },
                
                replyAndScore: function(commentHtml, commentWrapper, showCommentPostedMessage, commentReplyFormLi, commentHasChildren, loadMorePresentInThread, userLoggedIn) {
                
                    var shouldDisplayComment = false;
                    var elementToDisplayBelow = (commentHasChildren) ? 
                        commentReplyFormLi.nextUntil("li.comment:not(.comment-child)").last() : 
                        commentReplyFormLi;
                    
                    var scoreToAppearAbove = (userLoggedIn) ? 1 : 0;
                    commentReplyFormLi.nextUntil("li.comment:not(.comment-child)").each(function(i, element) {
                        element = $(element);
                        if(parseInt(element.find("span.score-sum").html()) <= scoreToAppearAbove) {
                            shouldDisplayComment = true;
                            elementToDisplayBelow = element.prev();
                            return false;
                        }
                    });
                    
                    if(!shouldDisplayComment) {
                        shouldDisplayComment = !loadMorePresentInThread();
                    }
                    
                    if(shouldDisplayComment) {
                        $(commentHtml).insertAfter(elementToDisplayBelow).wrapAll(commentWrapper);
                        return;
                    }
                    showCommentPostedMessage();
                },
                
                postAndScore: function(commentHtml, commentWrapper, showCommentPostedMessage, userLoggedIn) {
                
                    var shouldDisplayComment = false;
                    var elementToDisplayAbove;
                    
                    var scoreToAppearAbove = (userLoggedIn) ? 1 : 0;
                    $("li.comment:not(.comment-child)").each(function(i, element) {
                        element = $(element);
                        if(parseInt(element.find("span.score-sum").html()) <= scoreToAppearAbove) {
                            shouldDisplayComment = true;
                            elementToDisplayAbove = element;
                            return false;
                        }
                    });
                    
                    if(shouldDisplayComment) {
                        $(commentHtml).insertBefore(elementToDisplayAbove).wrapAll(commentWrapper);
                        return;
                    }
                    showCommentPostedMessage();
                }
            };
            
            // variable setup
            var commentReplyFormLi;
            var commentHasChildren;
            var loadMorePresentInThread;
            var commentWrapper;
            if(isReplyForm) {
                commentReplyFormLi = commentForm.closest("li.comment-reply-form");
                commentHasChildren = commentReplyFormLi.next("li.comment-child").length > 0;
                loadMorePresentInThread = function() {
                    var loadMoreExists = $("li.load-more-comments:not(:hidden)").length > 0;
                    var entriesUntilEndOfThread = commentReplyFormLi.nextUntil("li.comment:not(.comment-child)").length;
                    var entriesUntilLoadMore = commentReplyFormLi.nextUntil("li.load-more-comments").length;
                    return loadMoreExists && entriesUntilEndOfThread > entriesUntilLoadMore;
                };
                commentWrapper = "<li class='comment comment-child' />";
            } else {
                commentWrapper = "<li class='comment' />";
            }
            var showCommentPostedMessage = function() {
                $("p.comment-posted-successfully").removeClass("hidden");
            };
            
            // pick method based on sort order and whether this is a post or reply
            (function() {
                if(commentSortMethod == "newest" && isReplyForm) {
                    commentPlacementDelegates.replyAndNewest(commentHtml, commentWrapper, commentReplyFormLi);
                    return;
                }
                if(commentSortMethod == "newest" && !isReplyForm) {
                    commentPlacementDelegates.postAndNewest(commentHtml, commentWrapper);
                    return;
                }
                if(commentSortMethod == "oldest" && isReplyForm) {
                    commentPlacementDelegates.replyAndOldest(commentHtml, commentWrapper, showCommentPostedMessage, commentReplyFormLi, loadMorePresentInThread, commentHasChildren);
                    return;
                }
                if(commentSortMethod == "oldest" && !isReplyForm) {
                    commentPlacementDelegates.postAndOldest(commentHtml, commentWrapper, showCommentPostedMessage);
                    return;
                }
                if(commentSortMethod == "score" && isReplyForm) {
                    commentPlacementDelegates.replyAndScore(commentHtml, commentWrapper, showCommentPostedMessage, commentReplyFormLi, commentHasChildren, loadMorePresentInThread, userLoggedIn);
                    return;
                }
                if(commentSortMethod == "score" && !isReplyForm) {
                    commentPlacementDelegates.postAndScore(commentHtml, commentWrapper, showCommentPostedMessage, userLoggedIn);
                    return;
                }
                throw "Need to set which comment sort method has been used by assigning a value to commentSortMethod";
            })();
            
            // clean up form
            if(isReplyForm) {
                var parentLi = commentReplyFormLi.prev();
                parentLi.find("a.close-comment-reply").addClass("hidden");
                parentLi.find("a.open-comment-reply").removeClass("hidden");
                commentReplyFormLi.remove();
            } else {
                commentForm.find("textarea[name='comment']").val("");
            }
        });
        
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
                var editForm = commentContainer.children("div.comment-header").next();
                editForm.find("textarea[name='comment']").markdownPreview();
                editForm.find("input[name='preview']").remove();
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
        var clickedLink = $(this);
        
        clickedLink.closest("li.comment").next("li.comment-reply-form").addClass("hidden");
        
        clickedLink.addClass("hidden");
        clickedLink.siblings("a.open-comment-reply").removeClass("hidden");
        
        return false;
    });
    
    $("li.reply-to-comment > a.open-comment-reply").live('click', function() {
        $("li.comment-reply-form").addClass("hidden");
        $("a.close-comment-reply").addClass("hidden");
        $("a.open-comment-reply").removeClass("hidden");
        
        var clickedReplyLink = $(this);
        
        var commentLi = clickedReplyLink.closest("li.comment");
        var replyForm = commentLi.next("li.comment-reply-form");
        var replyFormExists = replyForm.length > 0;
        if(replyFormExists) {
            replyForm.removeClass("hidden");
        } else {
            $.get(clickedReplyLink.attr("data-ajax-url"), function(reply_form_html) {
                commentLi.after(reply_form_html);
                var replyForm = commentLi.next();
                replyForm.find("textarea[name='comment']").markdownPreview();
                replyForm.find("input[name='preview']").remove();
            });
        }
        
        clickedReplyLink.addClass("hidden");
        clickedReplyLink.siblings("a.close-comment-reply").removeClass("hidden");
        
        return false;
    });
    
    $("textarea[name='comment']").markdownPreview();
    $("input[name='preview']").remove();
    
});
