$(document).ready(function() {

    var ajaxLoaderHtml = "<div style='margin-bottom: 20px; padding-left: 100px; padding-top: 10px;'><img src='/media/images/ajax-loader.gif' alt='Loading...' style='display: inline; margin: 0px 5px 0px 0px;' /><span>Loading...</span></div>";
    var ajaxSubmittingHtml = "<div style='margin-bottom: 20px; margin-left: 131px; margin-top: -10px;'><img src='/media/images/ajax-loader.gif' alt='Loading...' style='display: inline; margin: 0px 5px 0px 0px;' /><span>Submitting...</span></div>";

    (function() {
        if($("div.comment-pagination").children("a[rel='next']").length > 0) {
            $("li.load-more-comments").show();
            $("div.comment-pagination").remove();
        }
    })();
    
    $("li.load-more-comments > a").live('click', function() {
        var loadMoreElement = $(this).parent();
        loadMoreElement.html(ajaxLoaderHtml);
        $.get($(this).attr("href"), function(commentListHtml) {
            $(commentListHtml).wrapAll("<div style='display: none;' />").parent().insertAfter(loadMoreElement);
            var lastComment = loadMoreElement.prev();
            loadMoreElement.remove();
            lastComment.next().slideDown(function() {
                $(this).children().unwrap();
                $("li.load-more-comments").show();
            });
        });
        return false;
    });

    $("form.edit-comment input[name='cancel']").live('click', function() {
        var commentContainer = $(this).closest("div.comment-nonscore");
        var commentHeader = commentContainer.children("div.comment-header");
        var commentBodyAndLinksDiv = commentContainer.children("div:hidden");
        commentContainer.children("form.edit-comment").fadeOut(null, function() {
            commentContainer.animate({height: commentHeader.height() + commentBodyAndLinksDiv.height()}, function() {
                commentBodyAndLinksDiv.fadeIn(null, function() {
                    $(this).children("blockquote.comment-body, ul.comment-links").unwrap();
                });
                var commentTextArea = commentContainer.find("textarea[name='comment']");
                commentTextArea.val(commentContainer.find("div.initial-comment").html());
                commentTextArea.trigger("change");
            });
        });
        return false;
    });
    
    $("form.edit-comment input[name='post']").live('click', function() {
        var editForm = $(this).closest("form.edit-comment");
        editForm.find("input[name='post']").remove();
        editForm.find("input[name='cancel']").remove();
        editForm.children().last().after(ajaxSubmittingHtml);
        $.post(editForm.attr("action"), editForm.serialize(), function(commentHtml) {
            var commentLi = editForm.closest("li.comment");
            commentLi.children().wrapAll("<div />").parent().fadeOut(function() {
                commentLi.children().wrap("<div />");
                commentLi.children().height(commentLi.children().children().height());
                commentLi.children().children().html(commentHtml);
                commentLi.children().animate({height: commentLi.children().children().height()}, function() {
                    commentLi.children().children().unwrap();
                    commentLi.children().fadeIn(function() {
                        $(this).children().unwrap();
                    });
                });
            });
        });
        return false;
    });
    
    $("form.post-comment input[name='cancel']").live('click', function() {
        var replyLi = $(this).closest("li.comment-reply-form");
        replyLi.stop(true, true).slideUp(function() {
            replyLi.find("input[type='text']").val("");
            var commentTextArea = replyLi.find("textarea[name='comment']");
            commentTextArea.val("");
            commentTextArea.trigger("change");
        });
        
        var parentLi = replyLi.prev();
        parentLi.find("a.close-comment-reply").hide();
        parentLi.find("a.open-comment-reply").show();
        
        return false;
    });
    
    $("form.post-comment input[name='post']").live('click', function() {
        var isInCommentList = $(this).closest("section#comments").length > 0;
        if(!isInCommentList) {
            return true;
        }
        
        var isReplyForm = $(this).closest("li.comment-reply-form").length > 0;
        var commentForm = $(this).closest("form");
        
        $.post(commentForm.attr("action"), commentForm.serialize(), function(commentHtml) {
            // check to see if this is an error page and load it into content if it is
            var isFullPage = $(commentHtml).find("div#content").length > 0;
            if(isFullPage) {
                $("div#content").html($(commentHtml).find("div#content").html());
                $("textarea[name='comment']").markdownPreview();
                $("input[name='preview']").remove();
                return false;
            }
            
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
                    var loadMorePresent = $("li.load-more-comments:not(:hidden)").length > 0;
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
                $("p.comment-posted-successfully").fadeIn(function() {
                    $(this).delay(3000).fadeOut();
                });
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
                parentLi.find("a.close-comment-reply").hide();
                parentLi.find("a.open-comment-reply").show();
                commentReplyFormLi.slideUp(function() {
                    commentReplyFormLi.remove();
                });
            } else {
                commentForm.find("input[type='text']").val("");
                var commentTextArea = commentForm.find("textarea[name='comment']");
                commentTextArea.val("");
                commentTextArea.trigger("change");
            }
        });
        
        return false;
    });
    
    $("li.comment-action-confirmation-required > a").live('click', function() {
        var clickedAnchor = $(this);
        clickedAnchor.hide();
        clickedAnchor.siblings("span.action-confirmation").show();
        return false;
    });
    
    $("li.comment-action-confirmation-required > span.action-confirmation > a.no").live('click', function() {
        var activeSpan = $(this).parent();
        activeSpan.hide();
        activeSpan.siblings("a:hidden").show();
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
        var commentHeader = commentContainer.children("div.comment-header");
        var editForm = commentContainer.children("form.edit-comment");
        var commentBodyAndLinks = commentContainer.children("blockquote.comment-body, ul.comment-links");
        var editFormExists = editForm.length;
        if(editFormExists) {
            commentBodyAndLinks.wrapAll("<div />").parent().fadeOut(function() {
                commentContainer.animate({height: commentHeader.height() + editForm.height()}, function() {
                    editForm.fadeIn();
                });
            });
        } else {
            commentBodyAndLinks.wrapAll("<div />").parent().fadeOut(null, function() {
                commentHeader.after(ajaxLoaderHtml);
                $.get(clickedAnchor.attr("data-ajax-url"), function(edit_form_html) {
                    commentHeader.next().remove();
                    commentHeader.after("<div style='display: none;' />").next().append(edit_form_html).children().hide().unwrap();
                    var editForm = commentContainer.children("div.comment-header").next();
                    var commentTextArea = editForm.find("textarea[name='comment']");
                    commentTextArea.markdownPreview();
                    $("<div class='initial-comment' style='display: none;' />").insertAfter(commentTextArea).append(commentTextArea.val());
                    editForm.find("input[name='preview']").remove();
                    commentContainer.animate({height: commentHeader.height() + editForm.height()}, function() {
                        editForm.fadeIn();
                    });
                });
            });
        }
        return false;
    });
    
    $("li.flag-comment > span.action-confirmation > a.yes").live('click', function() {
        var clickedAnchor = $(this);
        var parentSpan = $(this).parent();
        $.post(clickedAnchor.attr("href"), function() {
            parentSpan.hide();
            parentSpan.siblings("span.action-performed").show();
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
        var commentForm = clickedLink.closest("li.comment").next("li.comment-reply-form");
        
        commentForm.stop(true, true).slideUp(function() {
            commentForm.find("input[type='text']").val("");
            var commentTextArea = commentForm.find("textarea[name='comment']");
            commentTextArea.val("");
            commentTextArea.trigger("change");
        });
        
        clickedLink.hide();
        clickedLink.siblings("a.open-comment-reply").show();
        
        return false;
    });
    
    $("li.reply-to-comment > a.open-comment-reply").live('click', function() {
        $("li.comment-reply-form").stop(true, true).slideUp();
        $("a.close-comment-reply").hide();
        $("a.open-comment-reply").show();
        
        var clickedReplyLink = $(this);
        
        var commentLi = clickedReplyLink.closest("li.comment");
        var replyForm = commentLi.next("li.comment-reply-form");
        var replyFormExists = replyForm.length > 0;
        if(replyFormExists) {
            replyForm.stop(true, true).slideDown();
        } else {
            commentLi.after("<li style='display: none;' />").next().append(ajaxLoaderHtml);
            commentLi.next().slideDown(function() {
                $.get(clickedReplyLink.attr("data-ajax-url"), function(reply_form_html) {
                    commentLi.next().html(reply_form_html);
                    var replyForm = commentLi.next().children();
                    replyForm.hide().unwrap();
                    replyForm.find("textarea[name='comment']").markdownPreview();
                    replyForm.find("input[name='preview']").remove();
                    replyForm.stop(true, true).slideDown();
                });
            });
        }
        
        clickedReplyLink.hide();
        clickedReplyLink.siblings("a.close-comment-reply").show();
        
        return false;
    });
    
    $("textarea[name='comment']").markdownPreview();
    $("input[name='preview']").remove();
    
});
