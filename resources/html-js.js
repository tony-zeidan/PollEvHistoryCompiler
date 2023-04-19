function remove_all

document.addEventListener("DOMContentLoaded", function (e) {

    let groups = document.querySelectorAll(".responses");
    groups.forEach((group) => {

        let group_nodes = group.querySelectorAll("li");
        let correct_nodes = group.querySelectorAll(".correct");
        let incorrect_nodes = group.querySelectorAll(".incorrect");



        group_nodes.forEach(function (node) {
            if ("correct" in node.classList()) {
                node.addEventListener(function () {

                })
            }
        });
    });

});