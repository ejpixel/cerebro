$(document).ready(function() {

    $(".clickable").attr("edited", "false")
        .mouseenter(function(){
            $(this).find(".edition").fadeIn(100);
        })
        .mouseleave(function(){
            $(this).find(".edition").fadeOut(100);
        })
        .on("input", function() {
            $(this).attr("edited", "true");
        })
        .on('input', '.number', function() {
            if (!/^\d+$/.test($(this).text())) {
                $(this).text($(this).text().replace(/\D/g, ""))
            }
        })
        .on('input', '.float', function() {
            if (!/^[0-9]+(?:\.[0-9]{1,2})?$/.test($(this).text())) {
                $(this).text($(this).text().replace(/(?!^[0-9]+(?:\.[0-9]{1,2})?$)/g, ""))
            }
        })
        .on('input', '.text', function() {
            if (!/^[a-zA-Z0-9]+$/.test($(this).text())) {
                $(this).text($(this).text().replace(/(?![a-zA-Z]+)/g, ""))
            }
        });

    $(".edit").on("click", function () {
        let headers = [];
        let row = $(this).parent().parent();
        let data = row.find("td");
        row.parent().prev().find("tr > th").each(function() {
            header = [$(this).attr("class"), $(this).attr("type")];
            headers.push(header)
        });
        headers.map(function(element, i) {
            if (element[0] != null) {
               data.eq(i).attr("contenteditable", "true");
               data.eq(i).attr("class", element[1]);
               data.eq(i).css("background-color", "#F8F8FF")
            }
        })
    });

    $(".save").click(function() {
        let modified_list = [];
        let removed_list = [];
        let accepted_list = [];
        let headers = [];
        let target = $(this).prev().attr("id");
        $(this).prev().find("tr > th").each(function() {headers.push($(this).html())});

        $("tr").each(function() {
        let tRow = $(this);
            if (tRow.attr("edited") === "true" || tRow.attr("mark-removed") === "true" || tRow.attr("mark-accepted") === "true") {
                let modified = {};
                headers.map(function (element, i) {
                    modified[element] = tRow.find(`td:eq(${i})`).html()
                });
                if (tRow.attr("mark-removed") === "true") {
                    removed_list.push(modified)
                }

                else if (tRow.attr("edited") === "true") {
                    modified_list.push(modified)
                }


                if (tRow.attr("mark-accepted") === "true") {
                    accepted_list.push(modified)
                }

            }
        });
        if (modified_list.length > 0) {
            $.ajax({
                type: "POST",
                contentType: 'application/json; charset=utf-8',
                dataType: "json",
                url: "edit_" + target,
                data: JSON.stringify(modified_list),
                success: function() {location.reload()}
            });
        }

        else if (removed_list.length > 0) {
            $.ajax({
                type: "POST",
                contentType: 'application/json; charset=utf-8',
                dataType: "json",
                url: "remove_" + target,
                data: JSON.stringify(removed_list),
                success: function() {location.reload()}
            });
        }

        if (accepted_list.length > 0) {
            $.ajax({
                type: "POST",
                contentType: 'application/json; charset=utf-8',
                dataType: "json",
                url: "accept_" + target,
                data: JSON.stringify(accepted_list),
                success: function() {location.reload()}
            });
        }
    });

    $(".remove").on("click", function(){
        $(this).parent().find("button").each(function(i, e){$(e).fadeOut()});
        $(this).parent().append("<div class='temp-popup'><span>Do you really wants to remove this item?</span><button class='btn- btn-danger btn-sm remove-confirmation'>Yes</button><button class='btn- btn-primary btn-sm remove-negation'>No</button></div>");
        $(this).next().fadeIn()
    })

    $(".edition").hide()
        .on("click", ".remove-confirmation", function(){
            $(this).parent().parent().parent().attr("mark-removed", "true");
            $(this).parent().parent().parent().css("background-color", "red");
            $(this).parent().remove();
            $(".restore").fadeIn();
        })

        .on("click", ".remove-negation", function(){
            $(this).parent().parent().find("button").each(function(i, e){$(e).fadeIn()});
            $(this).parent().parent().find(".temp-popup").remove()
        })
        .on("click", ".restore", function() {
            $(this).parent().parent().attr("mark-removed", "false");
            $(this).parent().parent().attr("mark-accepted", "false");
            $(this).parent().parent().css("background-color", "");
            $(this).parent().find("button").each(function (i, e) {
                $(e).fadeIn()
            });
            $(this).fadeOut()
        })

    $(".accept").on("click", function(){
        $(this).parent().find(".remove").each(function(i, e){$(e).fadeOut()});
        $(this).parent().parent().attr("mark-accepted", "true");
        $(this).parent().parent().css("background-color", "green");
        $(this).fadeOut();
        $(".restore").fadeIn();
    });

    getPaymentsDataById();
    $("#service-id").on("change", getPaymentsDataById);


    function getPaymentsDataById() {
        let id = $("#service-id").val();
        $("#contracts").find("tbody tr").each(function(i, e){
            if ($(e).find("td:first").html() === id) {
                $("#payment").val(parseInt($(e).find("td").eq(13).html(), 10) + 1);
                $("#price").val($(e).find("td").eq(5).html())
                $("#quantity").val(1)
            }
        })
    }

    showHideView();
    function showHideView() {
        let id = $("#page-view").val();
        $("#" + id).show();
        $("#page-view option").each(function() {
            if ($(this).val() !== id) {
                $("#" + $(this).val()).hide();
            }
        })
    }

    $(".show").on("click", function(){
        let target = "#" + $(this).attr("refer");
        if ($(target).is(":visible")) {
            $(target).slideUp();
        }

        else {
            $(target).slideDown();
        }
    })

    function getNfeData() {
        $.ajax({
            type: "POST",
            contentType: 'application/json; charset=utf-8',
            dataType: "json",
            url: "get_contract_data",
            data: JSON.stringify({id: $("#service-id").val()}),
            success: function(response) {
                $("#cnae").val(response["cnae"]);
                $("#aliquota").val(response["aliquota"]);
                $("#cst").val(response["cst"]);
                $("#cfps").val(response["cfps"]);
                $("#aedf").val(response["aedf"]);
                $("#baseCalcSubst").val(response["baseCalcSubst"]);
                $("#codm").val(response["codm"]);
            }
        })
    }

    $("#page-view").on("change", showHideView);

    getNfeData();
    $("#service-id").on("change", getNfeData);
});
