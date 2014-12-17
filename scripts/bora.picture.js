$('#picClear').click(function()
{
    var fileinput = $("#imageinput");
    fileinput.replaceWith(fileinput.val('').clone(true));
});

$('#picUpload').click(function()
{
    var input = document.getElementById("imageinput");
    
    var len = input.files.length;
    
    if (len > 0) {
        var file = input.files[0];
        if (file.size > 0) {
            var formdata = new FormData();
            formdata.append(input.getAttribute('name'), file);
            
            $.ajax({
                url: '/upload/image',
                type: 'POST',
                data: formdata,
                cache: false,
                contentType: false,
                processData: false,
                success: function(res){
                    $("#contentInput").insertAtCursor(res + ' ');
                    var fileinput = $("#imageinput");
                    fileinput.replaceWith(fileinput.val('').clone(true));
                    }
                });
            }
        else {
            alert("The file '" + file.name + "' is empty!");
        }
    }
    
});

// this function from: http://richonrails.com/articles/text-area-manipulation-with-jquery
jQuery.fn.extend({
	insertAtCursor: function(myValue) {
		return this.each(function(i) {
			if (document.selection) {
				//For browsers like Internet Explorer
				this.focus();
				sel = document.selection.createRange();
				sel.text = myValue;
				this.focus();
			}
			else if (this.selectionStart || this.selectionStart == '0') {
				//For browsers like Firefox and Webkit based
				var startPos = this.selectionStart;
				var endPos = this.selectionEnd;
				var scrollTop = this.scrollTop;
				this.value = this.value.substring(0, startPos) + myValue + 
						    this.value.substring(endPos,this.value.length);
				this.focus();
				this.selectionStart = startPos + myValue.length;
				this.selectionEnd = startPos + myValue.length;
				this.scrollTop = scrollTop;
			} else {
				this.value += myValue;
				this.focus();
			}
		})
	}
});