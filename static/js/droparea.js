// implement JSON.stringify serialization
JSON.stringify = JSON.stringify || function (obj) {
    var t = typeof (obj);
    if (t != "object" || obj === null) {
        // simple data type
        if (t == "string") obj = '"'+obj+'"';
        return String(obj);
    }
    else {
        // recurse array or object
        var n, v, json = [], arr = (obj && obj.constructor == Array);
        for (n in obj) {
            v = obj[n]; t = typeof(v);
            if (t == "string") v = '"'+v+'"';
            else if (t == "object" && v !== null) v = JSON.stringify(v);
            json.push((arr ? "" : '"' + n + '":') + String(v));
        }
        return (arr ? "[" : "{") + String(json) + (arr ? "]" : "}");
    }
};


if(!Array.prototype.last) {
    Array.prototype.last = function() {
        return this[this.length - 1];
    }
}

function doneq_checker(obj) {
	console.log("Polling results from " + JSON.stringify(obj.data.url) + " for given object: " + JSON.stringify(obj) + "...");
	$.get(obj.data.url, { 'data' : JSON.stringify(obj.data) }, function(json) {
		if (json.data.done == false) {
			$.doTimeout( 300, function(){
				doneq_checker(json);
			});
		} else {
			console.log("All done. Now put the links to the site!!!");
			console.log("Last response was: " + JSON.stringify(json));
			console.log("Now showing results");
			for (var i = json.data.links.length - 1; i >= 0; i--){
				console.log(json.data.links[i]);
				$("#downloads").append("<li><a href='" + json.data.links[i] + "'>" + json.data.links[i].split('/').last() + "</a></li>")
			};
		}
	});	
}

(function( $ ){
    var s;
    // Methods
    var m = {
        init: function(e){},
        start: function(files,area){},
        complete: function(r){},
        error: function(r){ alert(r.error); return false; },
        traverse: function(files,area){
            if (typeof files !== "undefined") {
                for (var i=0, l=files.length; i<l; i++) {
                    m.upload(files[i], area);
                }
            } else {
                area.html(nosupport);
            }
        },
        upload: function(file, area){
            //area.empty();
            var progress = $('<div>',{
                'class':'progress'
            });
            area.append(progress);
			
            // File type control
            // if (typeof FileReader === "undefined" || !(/image/i).test(file.type)) {
			if (typeof FileReader === "undefined") {
                //area.html(file.type,s.noimage);
                alert('only image files: jpeg, png, gif');
                return false;
            }

            // File size control
            if (file.size > (s.maxsize * 1024)) {
                //area.html(file.type,s.maxsize);
                alert('max upload size: ' + s.maxsize + 'Kb');
                return false;
            }
			
            // Uploading - for Firefox, Google Chrome and Safari
            var xhr = new XMLHttpRequest();
            // Update progress bar
            xhr.upload.addEventListener("progress", function (e) {
                if (e.lengthComputable) {
                    var loaded = Math.ceil((e.loaded / e.total) * 100) + "%";
                    progress.css({
                        'height':loaded
                    }).html(loaded);
                }
            }, false);
			
            // File uploaded
            xhr.addEventListener("load", function (e) {
				console.log("got back after upload: " + e.target.responseText); // MTC
				var response = jQuery.parseJSON(e.target.responseText);
				doneq_checker(response);
				
                // var r = jQuery.parseJSON(e.target.responseText);
                // s.complete(r);
                // area.find('img').remove();
                // area.data('value',r.filename)
                // .append($('<img>',{'src': r.path + r.filename + '?' + Math.random()}));
                // progress.addClass('uploaded');
                // progress.html(s.uploaded).fadeOut('slow');
            }, false);
			
            xhr.open("post", s.post, true);
            
            // Set appropriate headers
            xhr.setRequestHeader("x-file-name", file.fileName);
            xhr.setRequestHeader("x-file-size", file.fileSize);
            xhr.setRequestHeader("x-file-type", file.type);
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

            // Set request headers
            for (var i in area.data())
                if (typeof area.data(i) !== "object")
                    xhr.setRequestHeader('x-param-'+i, area.data(i));

            var fd = new FormData();
            fd.append("x-file-name", file);
            xhr.send(fd);
        }
    };
    $.fn.droparea = function(o) {
        // Settings
        s = {
            'init': m.init,
            'start': m.start,
            'complete': m.complete,
            'instructions': 'Drop a file into this gray box',
            'over'        : 'drop file here!',
            'nosupport'   : 'No support for the File API in this web browser',
            'noimage'     : 'Unsupported file type!',
            'uploaded'    : 'Uploaded',
            'maxsize'     : '5000', //Kb
            'post'        : 'index'
        };
        this.each(function(){
            if(o) $.extend(s, o);
            var instructions = $('<div>').appendTo($(this));
            s.init($(this));            
            if(!$(this).data('value'))
                instructions.addClass('instructions').html(s.instructions);

            $(this)
            .bind({
                dragleave: function (e) {
                    e.preventDefault();
                    if($(this).data('value'))
                        instructions.removeClass().empty();
                    else
                        instructions.removeClass('over').html(s.instructions);
                },
                dragenter: function (e) {
                    e.preventDefault();
                    instructions.addClass('instructions over').html(s.over);
                },
                dragover: function (e) {
                    e.preventDefault();
                }
            });
            this.addEventListener("drop", function (e) {
                e.preventDefault();
                s.start(e.dataTransfer.files, $(this));
                m.traverse(e.dataTransfer.files, $(this));
                instructions.removeClass().empty();
            },false);
        });
    };
})( jQuery );
