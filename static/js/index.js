function like(photoid, user, image) {
    image = $(image);

    $.ajax({
        url: "/user/like",
        method: "POST",
        data: JSON.stringify({"id": photoid, "user": user}),
        contentType: 'application/json;charset=UTF-8',
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
            image.fadeOut(100);
            setTimeout(function() {
                var nextImage = image.next();
                nextImage.fadeIn(100);
                nextImage.removeClass("hide");
                var numLikes = parseInt(nextImage.next().text());
                nextImage.next().text(numLikes + 1);
            }, 100);
        }
        else {
            console.log("Error in liking");
        }
    });

}
