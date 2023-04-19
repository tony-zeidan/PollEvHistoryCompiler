$(document).ready(function () {
    
    $(".correct").click(function () {
        $(this).toggleClass('correct-selected');
    });

    $(".incorrect").click(function () {
        $(this).toggleClass('incorrect-selected');
    });
});