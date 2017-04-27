document.getElementById("upload").onclick = function() {
    return submitform();
}
document.getElementById("friend").onclick = function() {
    document.getElementById("addfriendform").submit();
}

var $form = $('#addphotoform')[0];

function submitform() {

    // Check if valid using HTML5 checkValidity() builtin function
    if ($form.checkValidity()) {
        $form.submit();
    }
    return false;
}

function readURL(input) {

    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            $('#preview').attr('src', e.target.result);
        }

        reader.readAsDataURL(input.files[0]);
    }
}

$("#file").change(function(){
    readURL(this);
});

function acceptrequest(fromperson, toperson, btn) {
    $.ajax({
        url: "/user/acceptrequest/" + fromperson + "/" + toperson,
        method: "GET"
        // data: $scope.user,
        // beforeSend: function(xhr, settings) {
        //     if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        //         xhr.setRequestHeader("X-CSRFToken", csrftoken);
        //     }
        //     xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        // }
    })
    .done(function (data) {
        var success = data["success"];
        console.log(data);
        if(success == 1) {
            console.log("Friend added");
            $(btn).removeClass("btn-primary");
            $(btn).addClass("btn-success");
            $(btn).addClass("disabled");
            $(btn).text("Accepted");
        }
        else {
            console.log("Error in adding friend");
        }
    });

}

$form.reset();
