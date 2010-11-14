(function( $ ) {

    $.fn.markdownPreview = function( options ) {
        
        var settings = {
            'insert-preview-div': true,
            'location': 'below',
            'preview-class-name': 'preview',
            'preview-element': null
        };
        
        if( options ) {
            $.extend( settings, options );
        }
        
        return this.each(function() {
            if(!settings['insert-preview-div'] && $(settings['preview-element']).length == 0) {
                throw "Either insert preview div should be set to true or an existing preview element needs to be provided";
            }
            
            $this = $(this)
            var previewElement = $(settings['preview-element']);
            
            if(settings['insert-preview-div']) {
                var previewElementHtml = '<div class="' + settings['preview-class-name'] + '" />';
                switch(settings['location']) {
                    case 'below':
                        $this.after(previewElementHtml);
                        previewElement = $this.next();
                        break;
                    case 'above':
                        $this.before(previewElementHtml);
                        previewElement = $this.prev();
                        break;
                    default:
                        throw settings['location'] + " is not a valid option for location";
                }
            }
            
            var converter = new Showdown.converter();
            $this.bind('keyup.markdown-preview', function() {
                previewElement.html(converter.makeHtml($this.val()));
            });
        });
        
    };

})( jQuery );
