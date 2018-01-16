/**
 * Created by cytng on 23/05/2017.
 */
var loading_Wheel_spin;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.loading_wheel_spin'), function (response) {
        loading_Wheel_spin = response;
    });
});

var loading_wheel;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.loading_wheel'), function (response) {
        loading_wheel = response;
    });
});

var no_name;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.no_name'), function (response) {
        no_name = response;
    });
});

var no_panel_name;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.no_panel_name'), function (response) {
        no_panel_name = response;
    });
});

var no_project_name;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.no_project_name'), function (response) {
        no_project_name = response;
    })
});

var no_regions;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.no_regions'), function (response) {
        no_regions = response;
    })
});

var not_unique;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.not_unique'), function (response) {
        not_unique = response
    })
});

var comp_message;
$(document).ready(function () {
    var name;
    if (window.location.href.indexOf('edit') > -1) {
        name = "edited"
    }
    else {
        name = "completed"
    }

    var data = $.get(Flask.url_for('panels.comp_message') + "?name=" + name, function (response) {
        comp_message = response
    })
});

var edit_region_start;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.edit_region') + "?type=start", function (response) {
        edit_region_start = response
    })
});

var edit_region_end;
$(document).ready(function () {
    var data = $.get(Flask.url_for('panels.edit_region') + "?type=end", function (response) {
        edit_region_end = response
    })
});

function ajax_error(xhr, status, error) {
    var trace = $('#trace');
    $(trace).children().remove();
    $(trace).append("<p>" + error + "</p>");
    $('#ajaxModal').modal('show');
    return false;
}

/**
 * When a region is added to the panel the final window message is changed
 */
function region_added() {
    var comp_messge = $('#complete_message');
    comp_messge.removeClass('alert-danger').addClass('alert-success');
    comp_messge.append(comp_message);
    var cancel = $('#cancel');
    cancel.removeClass('btn-danger').addClass('btn-success');
    cancel.text('Done!');
    cancel.attr('type', 'submit');
    $('#cancel_logo').removeClass('fa-remove').addClass('fa-check');
    $('#make_live').removeAttr('hidden');
}

/**
 * When create is cancelled the panel or virtual panel is removed from the database.
 * If vp_name is none, it uses the panel name.
 *
 * @param vp_name: the name of the virtual panel
 * @param panel_name: the name of the panel
 */
function remove_panel(vp_name, panel_name) {
    var dict = {};
    var url = "";
    var redirect = "";
    if (vp_name) {
        dict = {
            "vp_name": vp_name
        };
        url = Flask.url_for('panels.remove_vp');
        redirect = Flask.url_for('panels.create_virtual_panel_process');
    }
    else {
        dict = {
            "panel_name": panel_name
        };
        url = Flask.url_for('panels.remove_panel');
        redirect = Flask.url_for('panels.create_panel_process');
    }
    var data = JSON.stringify(dict);


    $.ajax({
        type: "POST",
        url: url,
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function () {
            window.location.replace(redirect);
        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }

    });
}

function unlock_panel() {
    var url = Flask.url_for('panels.toggle_locked');
    var id;
    if (window.location.href.indexOf('virtualpanels') > -1) {
        if ($('#main').attr('name') == 'main') {
            id = 'main'
        }
        else {
            id = $('#panel').val()
        }
    }
    else {
        id = $('#main').attr('name');
    }

    if (id == 'main') {
        return true;
    }
    else {
        var dict = {"id": id};
        var data = JSON.stringify(dict);
        $.ajax({
            type: "POST",
            url: url,
            data: data,
            dataType: "json",
            contentType: "application/json",
            success: function () {
                return true;
            },
            error: function (xhr, status, error) {
                return ajax_error(xhr, status, error)
            }
        })
    }
}

/**
 * When cancel is clicked, js checks if in create or edit wizard and executes appropriate function.
 * Edit is redirected to view panel and create removes the panel from the database.
 */
$(document).on('click', '#cancel', function () {
    var vpanel = $('#vpanelname');
    var vp_name = vpanel.val();
    var panel_name = $('#panelname').val();
    if ($('#cancel').hasClass('btn-danger') && window.location.pathname.indexOf("wizard") >= 0) {
        unlock_panel();
        remove_panel(vp_name, panel_name)
    }
    else if (window.location.pathname.indexOf("edit") >= 0) {
        if (vpanel.length) {
            unlock_panel();
            var url = Flask.url_for('panels.view_vpanel') + '?id=' + $('#main').attr('name');
            window.location.replace(url);
        }
        else {
            unlock_panel();
            window.location.replace(Flask.url_for('panels.view_panels'));
        }
    }
});

/**
 * Method to add a panel or virtual panel to the database and unlock the other wizard tabs.
 * Method determines if panel or virtual panel needs to be added.
 *
 * @param changeTab: indicates that back or next have been clicked. If none, tab page clicked is selected (e)
 * @param e: Tab page that has been clicked
 */
function add_panel(changeTab, e) {
    var dict = {};
    var url = "";
    var redirect = "";
    var vpanel = $('#vpanelname');
    var msg = $('#message');
    var panel = $('#panel');
    console.log('val length');
    console.log();
    if ($(vpanel).length) {
        if (panel.val() == "__None") {
            // new_html = "<div class=\"alert alert-danger\"><strong>Silly Sausage!</strong> You haven't selected a panel name</div>";
            // msg.append(new_html);
            $(msg).append(no_panel_name);
            return false;
        }
        else if ($(vpanel).val().length == 0) {
            $(msg).append(no_name);
            return false;
        }
    }
    else if ($('#panelname').length) {
        if( $('#project').val() == "__None") {
            // new_html = "<div class=\"alert alert-danger\"><strong>Silly Sausage!</strong> You haven't selected a project name</div>";
            // msg.append(new_html);
            $(msg).append(no_project_name);
            return false;
        }
        else if($('#panelname').val().length == 0){
            $(msg).append(no_name);
            return false;
        }
    }

    if (vpanel.length) {
        dict = {
            "vp_name": vpanel.val(),
            "panel_name": null,

            "panel_id": panel.val(),
            "project_id": null
        };
        url = Flask.url_for('panels.add_vp');
        redirect = Flask.url_for('panels.create_virtual_panel_process') + "?id=";
    }
    else {
        dict = {
            "vp_name": null,
            "panel_name": $('#panelname').val(),

            "panel_id": null,
            "project_id": $('#project').val()
        };
        url = Flask.url_for('panels.add_panel');
        redirect = Flask.url_for('panels.create_panel_process') + "?id=";
    }
    var data = JSON.stringify(dict);
    var complete = false;
    $.when($.ajax({
        type: "POST",
        url: url,
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function (response) {
            if (response == -1) {
                // new_html = "<div class=\"alert alert-danger\"><strong>Silly Sausage!</strong> That name isn't unique</div>";
                // msg.append(new_html)
                $(msg).append(not_unique)
            }
            else {
                var newUrl = redirect + response;
                var main = $('#main');
                main.attr('name', response);
                main.attr('action', newUrl);
                $('.glyphicon-transfer').attr('href', '#select_tx');
                $('.glyphicon-list-alt').attr('href', '#select_genes');
                $('.glyphicon-th-large').attr('href', '#select_regions');
                $('.glyphicon-ok').attr('href', '#submit_vp');
                $("#vpanelname").attr("disabled", "disabled");
                $("#panel").attr("disabled", "disabled");
                $("#panelname").attr("disabled", "disabled");
                $("#project").attr("disabled", "disabled");
                $('.glyphicon.glyphicon-new-selected').removeClass('glyphicon-new-selected').addClass('glyphicon-new');

                complete = true;

                if (changeTab == 'next' || changeTab == 'back') {
                    change_tab(changeTab)
                }
                else {
                    var target = $('#' + e);
                    target.removeClass('glyphicon-new').addClass('glyphicon-new-selected').blur();
                    target.tab('show');
                }
            }
        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }
    })).done(function () {
        return complete;
    });

}

$(document).on('click', '.glyphicon', function (j) {

    $('#message').children().remove();

    if ($('.glyphicon-new-selected').attr('href') == '#initialise' && $("#vpanelname").attr("disabled") != "disabled" && $("#panelname").attr("disabled") != "disabled") {
        add_panel(false, $(j.target).attr('id'));
    }
    else if ($(j.target).hasClass('glyphicon-new') || $(j.target).hasClass('glyphicon-new-selected')) {
        $('.glyphicon.glyphicon-new-selected').removeClass('glyphicon-new-selected').addClass('glyphicon-new');
        $(this).addClass('glyphicon-new-selected').removeClass('glyphicon-new').blur();
    }
});

function change_tab(tabChange) {
    var activeTab = $('.tab-pane.active');
    if (tabChange == 'next') {
        var nextTab = activeTab.next('.tab-pane').attr('id');
        var nextTab_elem = $('[href="#' + nextTab + '"]');
        nextTab_elem.addClass('glyphicon-new-selected').removeClass('glyphicon-new');
        nextTab_elem.tab('show');
    }
    else {
        var prevTab = activeTab.prev('.tab-pane').attr('id');
        var prevTab_elem = $('[href="#' + prevTab + '"]');
        prevTab_elem.addClass('glyphicon-new-selected').removeClass('glyphicon-new');
        prevTab_elem.tab('show');
    }
}

$(document).on('click', '.next-step, .prev-step', function (e) {
    var activeTab = $('.tab-pane.active');
    $('#message').children().remove();
    var tab = 'back';
    var target;
    if ($(e.target).is("button")) {
        target = $(e.target)
    }
    else {
        target = $(e.target).parent()
    }
    if ($(target).hasClass('next-step')) {
        tab = 'next'
    }
    if ($(activeTab).attr('id') == "initialise" && $('#panelname').attr('disabled') != 'disabled' && $("#vpanelname").attr("disabled") != "disabled") {
        add_panel(tab, $(e))
    }
    else {
        $('.glyphicon.glyphicon-new-selected').removeClass('glyphicon-new-selected').addClass('glyphicon-new');
        change_tab(tab)
    }
});

$(document).on('change', '#panel', function () {
    $('#geneselector').children().remove();
    $('#loading').append(loading_wheel);

    var panel_id = $('#panel').val();

    if (panel_id == "__None") {
        return false;
    }
    var dict = {
        "panel": panel_id
    };
    var data = JSON.stringify(dict);

    $.ajax({
        type: "POST",
        url: Flask.url_for('panels.select_vp_genes'),
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function (response) {
            $('#loading').children().remove();
            $('#geneselector').append(response)
        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }

    });
});

$(document).on('focusin', '[name="region_start"]', function () {
    var row = $(event.target).parent().parent();
    var td = $(row).children().eq(5);
    var div = $(td).children().eq(0);
    var region_id = $(row).children().eq(0).children().eq(0).attr('for');
    if ($.inArray(parseInt(region_id), JSON.parse(sessionStorage.getItem("current_ids"))) > -1) {
        var current = sessionStorage.getItem(region_id);
        var dict = {};
        var arr = {"value": $(event.target).val(), "html": $(div).prop('outerHTML')};
        if (current == null) {
            dict["start"] = arr;
        }
        else {
            dict = JSON.parse(current);
            dict["start"] = arr;
        }
        sessionStorage.setItem(region_id, JSON.stringify(dict));
        $($(td).children()).remove();
        $(td).append(edit_region_start);
    }
});

$(document).on('focusout', '[name="region_start"]', function (e) {
    if ($(e.relatedTarget).attr('name') != 'update') {
        var target = $(event.target);
        var row = $(event.target).parent().parent();
        // this section populates row and target correctly if event is triggered by check_regions() returning false
        if ($(row).hasClass('list-unstyled')) {
            row = $(row).parent().parent();
            target = $(row).children().eq(2).children().eq(0);
        }
        else if ($(row).parent().hasClass('list-unstyled')) {
            row = $(row).parent().parent().parent();
            target = $(row).children().eq(2).children().eq(0);
        }
        //
        var region_id = $(row).children().eq(0).children().eq(0).attr('for');
        var td = $(row).children().eq(5);
        var store = JSON.parse(sessionStorage.getItem(region_id));
        if (store == null) {
        }
        else if (!"start" in store) {
        }
        else if ($(target).val() == store["start"]["value"]) {
            $($(td).children()).remove();
            $(td).append(store["start"]["html"]);
            $(td).children().eq(0).children().eq(0).prop('checked', true);
        }
    }
});

$(document).on('focusin', '[name="region_end"]', function () {
    var row = $(event.target).parent().parent();
    var td = $(row).children().eq(5);
    var div = $(td).children().eq(0);
    var region_id = $(row).children().eq(0).children().eq(0).attr('for');
    if ($.inArray(parseInt(region_id), JSON.parse(sessionStorage.getItem("current_ids"))) > -1) {
        var current = sessionStorage.getItem(region_id);
        var dict = {};
        var arr = {"value": $(event.target).val(), "html": $(div).prop('outerHTML')};
        if (current == null) {
            dict["end"] = arr;
        }
        else {
            dict = JSON.parse(current);
            dict["end"] = arr;
        }
        sessionStorage.setItem(region_id, JSON.stringify(dict));
        $($(td).children()).remove();
        $(td).append(edit_region_end);
    }
});

$(document).on('focusout', '[name="region_end"]', function (e) {
    if ($(e.relatedTarget).attr('name') != 'update') {
        var target = $(event.target);
        var row = $(event.target).parent().parent();
        // this section populates row and target correctly if event is triggered by check_regions() returning false
        if ($(row).hasClass('list-unstyled')) {
            row = $(row).parent().parent();
            target = $(row).children().eq(2).children().eq(0);
        }
        else if ($(row).parent().hasClass('list-unstyled')) {
            row = $(row).parent().parent().parent();
            target = $(row).children().eq(2).children().eq(0);
        }
        //
        var region_id = $(row).children().eq(0).children().eq(0).attr('for');
        var td = $(row).children().eq(5);
        var store = JSON.parse(sessionStorage.getItem(region_id));
        if (store == null) {
        }
        else if (!"end" in store) {
        }
        else if ($(target).val() == store["end"]["value"]) {
            $($(td).children()).remove();
            $(td).append(store["end"]["html"]);
            $(td).children().eq(0).children().eq(0).prop('checked', true);
        }
    }
});

function checkRegions(row, changed, prev) {
    var startBox = $(row).children().eq(2).children().eq(0);
    var endBox = $(row).children().eq(3).children().eq(0);
    if ($(startBox).val() > $(endBox).val()) {
        $('#regionModal').modal('show');
        if (changed == 'start') {
            $(startBox).val(prev);
            $(startBox).trigger('focusout')
        }
        else {
            $(endBox).val(prev);
            $(endBox).trigger('focusout')
        }
        return false
    }
    var newVal;
    var cdsVal;
    if (changed == 'start') {
        newVal = $(startBox).val();
        cdsVal = $(startBox).attr('cds');

        if (newVal > cdsVal) {
            $('#cdsModal').modal('show');
            return false
        }
    }
    else {
        newVal = $(endBox).val();
        cdsVal = $(endBox).attr('cds');

        if (newVal < cdsVal) {
            $('#cdsModal').modal('show');
            return false
        }
    }

    return true
}

$(document).on('click', '#region-ok', function () {

    var button = $('[name="update"]');
    var row = $(button).parent().parent().parent().parent();
    var region_id = $(row).children().eq(0).children().eq(0).attr('for');
    var store = JSON.parse(sessionStorage.getItem(region_id));

    update_region($(row), store, region_id);

});

$(document).on('click', '#region-cancel', function () {
    $('[name="undo"]').trigger('click');

});

function update_region(row, store, region_id) {
    var ext_3 = null;
    var ext_5 = null;
    var new_val;
    var no_ext;

    if ("start" in store) {
        new_val = $(row).children().eq(2).children().eq(0).val();
        no_ext = $(row).children().eq(2).children().eq(0).attr('id');
        ext_5 = no_ext - new_val
    }

    if ("end" in store) {
        new_val = $(row).children().eq(3).children().eq(0).val();
        no_ext = $(row).children().eq(3).children().eq(0).attr('id');
        ext_3 = new_val - no_ext
    }

    $(event.target).removeClass('glyphicon-floppy-disk').addClass('glyphicon-refresh glyphicon-refresh-animate');

    var dict = {
        "region_id": region_id,
        "panel_id": $('#main').attr('name'),
        "ext_3": ext_3,
        "ext_5": ext_5
    };

    var data = JSON.stringify(dict);

    $.ajax({
        type: "POST",
        url: Flask.url_for('panels.update_ext'),
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function () {
            var td = $(row).children().eq(5);
            $($(td).children()).remove();
            var html;
            if ("start" in store) {
                html = store["start"]["html"];
                $(td).parent().children().eq(2).children().eq(0).removeAttr('style')
            }
            else {
                html = store["end"]["html"];
                $(td).parent().children().eq(3).children().eq(0).removeAttr('style')
            }
            $(td).append(html);
            $(td).children().eq(0).children().eq(0).prop('checked', true);
            region_added()

        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }

    });
}

$(document).on('click', '[name="update"]', function () {
    var row;
    if ($(event.target).attr('name') == 'update') {
        row = $(event.target).parent().parent().parent().parent();
    }
    else {
        row = $(event.target).parent().parent().parent().parent().parent();
    }

    var region_id = $(row).children().eq(0).children().eq(0).attr('for');
    console.log(region_id);
    var store = JSON.parse(sessionStorage.getItem(region_id));

    var complete;
    console.log(store);
    if ("start" in store) {
        if (store["start"]["value"] == $(row).children().eq(2).children().eq(0).val()) {
            $(row).children().eq(2).children().eq(0).trigger('focusout');
            // return
        }
        complete = checkRegions(row, 'start', store["start"]["value"]);
    }
    if ("end" in store) {
        if (store["end"]["value"] == $(row).children().eq(3).children().eq(0).val()) {
            $(row).children().eq(3).children().eq(0).trigger('focusout');
        }
        complete = checkRegions(row, 'end', store["end"]["value"]);
    }
    console.log('complete');
    console.log(complete);
    if (complete) {
        update_region(row, store, region_id)
    }


});

$(document).on('click', '[name="undo"]', function (e) {
    var row;
    if ($(event.target).attr('name') == 'undo') {
        row = $(event.target).parent().parent().parent().parent();
    }
    else {
        row = $(event.target).parent().parent().parent().parent().parent();
    }
    var region_id = $(row).children().eq(0).children().eq(0).attr('for');
    var store = JSON.parse(sessionStorage.getItem(region_id));
    var html;
    if ("start" in store) {
        $(row).children().eq(2).children().eq(0).val(store["start"]["value"]);
        html = store['start']['html']
    }

    if ("end" in store) {
        $(row).children().eq(3).children().eq(0).val(store["end"]["value"]);
        html = store['end']['html']
    }

    var td = $(row).children().eq(5);
    $($(td).children()).remove();
    $(td).append(html);
    $(td).children().eq(0).children().eq(0).prop('checked', true);
});

$(document).on('click', '.label-gene', function () {
    var target = $(this);
    var gene_switch;
    var geneName = '';
    if ($(target).is("button")) {
        geneName = $(target).attr('name');
        $('.label-gene').each(function (i, obj) {
            if ($(obj).attr('for') == geneName) {
                gene_switch = $(obj);
                return false;
            }
        });
    }
    else {
        geneName = $(target).attr('for');
        gene_switch = $(target)
    }
    var input = $(gene_switch).parent().children().eq(0);
    if ($(gene_switch).attr('disabled') != 'disabled') {
        if ($(input).prop('checked'))//remove gene button
        {
            $('[name="genebutton"]').each(function (i, obj) {
                if ($(obj).attr('data-name') == geneName) {
                    $(obj).remove();
                    if ($('#remove-gene').attr('name') == geneName) {
                        $('#regions').children().remove();
                    }
                    return false;
                }
            });
            console.log('hello');
            console.log($('#genelist').html());
            console.log($('#genelist').html().search(/&nbsp;\s+&nbsp;/));
            $('#genelist').html($('#genelist').html().replace(/&nbsp;\s+&nbsp;/, "&nbsp;"));
            var select_all = $('#all-genes');
            if (select_all.prop('checked')) {
                select_all.attr('uncheck-all', 'false');
                select_all.trigger('click')
            }

        }
        else {
            var geneId = $("#" + geneName).attr('name');
            $.get(Flask.url_for('panels.add_to_genelist') + "?name=" + geneName + "&id=" + geneId, function (data) {
                $('#genelist').append(data)
            });
            if (count_genes() == 0) {
                $('#add-all').attr('disabled', 'disabled')
            }
            else if ($('#add-all-vp').attr('disabled') == 'disabled') {
                $('#add-all-vp').removeAttr('disabled')
            }
        }
    }
});

$(document).on('click', '[id^="btnO"]', function () {
    var notchecked = $('input[type="radio"][name="menucolor"]').not(':checked');
    //$('.navbar.'+notchecked.val()).toggleClass('navbar-default navbar-inverse');
    notchecked.prop("checked", true);
    $(this).parent().find('a').each(function () {
        if ($(this).attr('id') == 'btnOn') {
            $(this).toggleClass('active btn-success btn-default');
        } else {
            $(this).toggleClass('active btn-danger btn-default');
        }

    });
    doChange(notchecked);
});

$(document).on('change', 'input[type="radio"][name="menucolor"]', function () {
    doChange(this);
});

function doChange() {
    var btnOnGlyph = $('#btnOn .glyphicon-ok');
    var btnOffGlyph = $('#btnOff .glyphicon-remove');
    console.log(btnOnGlyph.attr('style'));
    if (btnOnGlyph.attr('style') == 'opacity:0;') {
        $('#btnOff').removeClass('active');
        btnOffGlyph.attr('style', 'opacity: 0;');
        btnOnGlyph.attr('style', 'opacity: 1;');
        $('#btnOn').focus();
    }
    else {
        $('#btnOn').removeClass('active');
        btnOnGlyph.attr('style', 'opacity: 0;');
        btnOffGlyph.attr('style', 'opacity: 1;');
        $('#btnOff').focus();
    }

    $('#region-table').remove();
    $('#regions').append(loading_wheel);
    get_regions($('.btn-warning'));
}

$(document).on('click', '#create-regions', function () {
    $('#add-custom-region').removeAttr('style');
});

$(document).on('click', '#add-custom', function () {
    var custom_message = $('#custom-message');
    custom_message.attr('style', "display: none;");
    custom_message.html("");
    var chrom = $('#chrom').val();
    var start = parseInt($('#start-pos').val());
    var end = parseInt($('#end-pos').val());
    var name = $('#region-name').val();
    var message = '';
    if (chrom == 0) {
        message = "You haven't picked a chromosome"
    }
    else if (start.length == 0) {
        message = 'The start position is not defined'
    }
    else if (end.length == 0) {
        message = 'The end position is not defined'
    }
    else if (name.length == 0) {
        message = 'The region name is not defined'
    }
    else if (start > end) {
        message = "The start position is greater the end position"
    }
    else if (!/^[a-z0-9:._\->+]+$/i.test(name)) {
        message = "The name field can only contain numbers, letters and the following special characters ': . _ - + >'"
    }
    console.log(encodeURIComponent(message));
    if (message != '') {
        custom_message.load(Flask.url_for('panels.custom_message') + "?message=" + encodeURIComponent(message));
        custom_message.removeAttr('style')
    }
    else {
        var dict = {
            "panel_id": $('#main').attr('name'),
            "chrom": chrom,
            "start": start,
            "end": end,
            "name": name
        };
        var data = JSON.stringify(dict);

        $.ajax({
            type: "POST",
            url: Flask.url_for('panels.create_panel_custom_regions'),
            data: data,
            dataType: "json",
            contentType: "application/json",
            success: function () {
                $('#add-custom-region').attr('style', "display: none;");
                $('#chrom').val(0);
                $('#start-pos').val('');
                $('#end-pos').val('');
                $('#region-name').val('');

                $('#region-table').remove();
                $('#regions').append(loading_wheel);

                get_regions($('.btn-custom'));
                region_added()
            },
            error: function (xhr, status, error) {
                return ajax_error(xhr, status, error)
            }

        });
    }
});

function count_genes() {
    var not_added = 0;
    $('.btngene').each(function (i, obj) {
        if ($(obj).children().eq(0).hasClass('glyphicon-pencil')) {
            not_added += 1
        }
    });
    return not_added
}


function get_regions(element) {
    var gene_id = $(element).attr('data-id');
    var gene_name = $(element).attr('data-name');
    var panel_id = '';
    var vpanel_id = '';
    var include_utr = false;
    var panel = $('#panel');
    if (panel.length) {
        panel_id = panel.val();
        vpanel_id = $('#main').attr('name');
    }
    else {
        console.log('$(\'#regions\').children().length');
        console.log($('#regions').children());
        panel_id = $('#main').attr('name');
        if ($('#btnOn').hasClass('active')) {
            include_utr = true;
        }
        else if ($(element).children(0).hasClass("glyphicon-ok")) {
            include_utr = "added"
        }
        vpanel_id = null;
    }
    console.log(include_utr);
    var dict = {
        "panel_id": panel_id,
        "gene_id": gene_id,
        "gene_name": gene_name,
        "vpanel_id": vpanel_id,
        "include_utr": include_utr
    };
    var data = JSON.stringify(dict);

    var url = '';
    if ($(element).hasClass('btn-custom')) {
        url = Flask.url_for('panels.get_custom_regions');
    }
    else {
        url = Flask.url_for('panels.edit_vp_regions');
    }
    $.ajax({
        type: "POST",
        url: url,
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function (response) {
            var regions = $('#regions');
            regions.children().remove();
            regions.append(response['html']);
            var ids = response['ids'];
            console.log(ids);
            try {
                for (var key in response['store']) {
                    if (response['store'].hasOwnProperty(key)) {
                        sessionStorage.setItem(key, JSON.stringify(response['store'][key]));
                    }
                }
            }
            catch (err) {
                console.log('error')
            }

            sessionStorage.setItem("current_ids", JSON.stringify(response['ids']));
            console.log('success');
            $('.label-region').each(function (i, obj) {
                console.log('hello');
                //this gets the third parent of the label (tr)
                var row = $(obj).parent().parent().parent();
                //this get the third child (index 2) of the row and the child of that row is the text box
                //check that ID is in list and
                var style = $($($($(row[0])).children().eq(2)[0])[0]).children().eq(0).attr('style');
                if (($.inArray(parseInt($(obj).attr("for")), JSON.parse(sessionStorage.getItem("current_ids"))) > -1 && style != "color:red;") || ($.inArray(parseInt($(obj).attr("for")), JSON.parse(sessionStorage.getItem("current_ids"))) == -1 && style == "color:red;")) {
                    console.log('click');
                    $(obj).trigger('click')
                }
            });
        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }

    });
}

$(document).on('click', '[name="genebutton"]', function (request) {
    var add_custom = $('#add-custom-region');
    var regions = $('#regions');
    if (add_custom.attr("style") == null) {
        add_custom.attr("style", "display: none;")
    }
    regions.children().remove();
    regions.append(loading_wheel);
    var element = $(request.currentTarget);
    $('.btn-warning').each(function (i, obj) {
        if ($(obj.firstElementChild).hasClass('glyphicon-ok')) {
            $(obj).removeClass('btn-warning').addClass('btn-success')
        }
        else {
            $(obj).removeClass('btn-warning').addClass('btn-danger')
        }
    });
    $(element).removeClass("btn-danger").removeClass("btn-success").addClass("btn-warning").blur();
    get_regions($(element));

});

function count_ids() {
    var ids = [];
    $('.label-region').each(function (i, obj) {
        var check = $(obj).parent().children().eq(0);

        if ($(check).prop('checked')) {
            ids.push($(obj).attr('for'));
        }
    });
    return ids
}

$(document).on('click', ".label-region", function (request) {
    var obj = $(request.currentTarget);
    var check = $(obj).parent().children().eq(0);
    var select_all = $('.label-selectall');

    var count = count_ids().length;
    if (count == 1 && $(check).prop('checked')) {
        $('#add-regions').attr('disabled', 'disabled');
    }
    else if (count > 0 || (count == 0 && !$(check).prop('checked'))) {
        $('#add-regions').removeAttr('disabled');
    }
    else if ($('#add-regions').attr('disabled') != 'disabled') {
        $('#add-regions').attr('disabled', 'disabled');
    }

    if (((count == $('.label-region').length - 1 && !$(check).prop('checked')) || //if the count is one less than the total and the current target is about to be "checked"
            (count == 1 && $(check).prop('checked'))) && //if the count is one and the current target is about to be "unchecked"
        select_all.attr('clicked') != "clicked") { //if the selectall slider has not been clicked
        select_all.attr('uncheck-all', 'false');
        select_all.trigger('click')
    }
    else if ($(check).prop('checked') && $(select_all.parent().children().eq(0)).prop('checked')//if the current target is being "unchecked" and the selectall button is checked
        && select_all.attr('clicked') != "clicked") { //if the selectall slider has not been clicked
        select_all.attr('uncheck-all', 'false');
        select_all.trigger('click')
    }
});

$(document).on('change', '#all-genes', function (e) {
    var all_genes = $('#all-genes');
    if ($(all_genes).prop('checked')) {//if select all has been clicked on

        $('.label-gene').each(function (i, obj) {
            var check = $(obj).parent().children().eq(0);
            if (!$(check).prop('checked')) {
                $(obj).trigger('click')
            }
        })

    }
    else {
        if ($(all_genes).attr('uncheck-all') == 'false') {
            $(all_genes).removeAttr('uncheck-all')
        }
        else {
            $('.label-gene').each(function (i, obj) {
                var check = $(obj).parent().children().eq(0);
                if ($(check).prop('checked')) {
                    $(obj).trigger('click')
                }
            })
        }
    }
});

$(document).on('click', ".label-selectall", function () {
    var select_all = $('.label-selectall');
    var select_check = $(select_all).parent().children().eq(0);
    select_all.attr('clicked', 'clicked');
    if (select_all.attr('uncheck-all') == 'false')//if one region has been (un)selected (not all regions need to be deselected)
    {
        select_all.removeAttr('uncheck-all')
    }
    else if (select_check.prop('checked')) //if select all has been clicked off
    {
        $(".label-region").each(function (i, obj)//loop through all elements with .label-region class
        {
            var check = $(obj).parent().children().eq(0);
            if ($(check).prop('checked'))//if object is checked turn it off
            {
                $(obj).trigger('click');
            }
        });
    }
    else //if select all has been clicked on
    {
        console.log('else');
        if (select_all.attr('uncheck-all') == 'false') {
        }
        else {
            $(".label-region").each(function (i, obj)//loop through all elements with .label-region class
            {
                var check = $(obj).parent().children().eq(0);
                if (!$(check).prop('checked'))//if object is selected do nothing
                {
                    $(obj).trigger('click')
                }
            });
        }

    }

    select_all.removeAttr('clicked');

});

$(document).on('click', "#remove-gene", function () {
    var geneName = $('#remove-gene').attr('name');
    var ids;
    var label_gene = $('.label-gene');
    label_gene.each(function (i, obj) {
        if ($(obj).attr('for') == geneName) {
            $(obj).removeAttr('disabled');
            $(obj).removeClass('label-added').addClass('label-success');
            var name = $(obj).attr('for');
            $('#' + name).removeAttr('disabled');
            $(obj).trigger('click');
            return false;
        }
    });

    if (sessionStorage.getItem('current_ids') && $('#vpanelname').length) {
        var vpanel_id = $('#main').attr('name');
        ids = sessionStorage.getItem('current_ids');
        if (JSON.parse(sessionStorage.getItem("current_ids")).length > 0) {
            remove_vp_regions(vpanel_id, ids);
            region_added()
        }
        else {
            $('#regions').children().remove();
        }
    }
    else if (sessionStorage.getItem('current_ids') && $('#panelname').length) {
        var panel_id = $('#main').attr('name');
        ids = sessionStorage.getItem('current_ids');

        $('[name="genebutton"]').each(function (i, obj) {
            if ($(obj).attr('data-name') == geneName) {
                $(obj).remove()
            }
        });
        console.log('hello');
        console.log($('#genelist').html());
        $('#genelist').html($('#genelist').html().replace(/&nbsp;\s+&nbsp;/, "&nbsp;"));
        var row = $('#' + geneName).parent().parent().parent();
        $(row[0]).remove();
        if (JSON.parse(sessionStorage.getItem("current_ids")).length > 0) {
            remove_panel_regions(panel_id, ids, geneName);
            region_added()
        }
        else {
            $('#regions').children().remove();
        }
    }
    else {
        $('#regions').children().remove();
    }
});

function remove_vp_regions(vpanel_id, ids, geneName) {
    var dict = {
        "vp_id": vpanel_id,
        "ids": ids
    };
    var data = JSON.stringify(dict);
    $.ajax({
        type: "POST",
        url: Flask.url_for('panels.remove_vp_regions'),
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function (response) {
            if (response == 0) {
                var complete = $('#complete_message');
                complete.addClass('alert-danger').removeClass('alert-success');
                complete.append(no_regions);
                var cancel = $('#cancel');
                cancel.addClass('btn-danger').removeClass('btn-success');
                cancel.text('Cancel');
                cancel.removeAttr('type');
                $('#cancel_logo').addClass('fa-remove').removeClass('fa-check');
                $('#make_live').attr('hidden', 'hidden')
            }

            $('[name="genebutton"]').each(function (i, obj) {
                if ($(obj).attr('data-name') == geneName) {
                    $(obj).children('.glyphicon-pencil').removeClass('glyphicon-pencil').addClass('glyphicon-ok').blur();
                    $(obj).removeClass('btn-warning').addClass('btn-success').blur();
                }
            });

            $('#regions').children().remove();
            region_added()
        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }

    });
}

function remove_panel_regions(panel_id, ids, gene_name) {
    var dict = {
        "panel_id": panel_id,
        "ids": ids
    };
    var data = JSON.stringify(dict);
    $.ajax({
        type: "POST",
        url: Flask.url_for('panels.remove_panel_regions'),
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function (response) {
            if (response == 0) {
                var complete = $('#complete_message');
                complete.addClass('alert-danger').removeClass('alert-success');
                complete.append(no_regions);
                var cancel = $('#cancel');
                cancel.addClass('btn-danger').removeClass('btn-success');
                cancel.text('Cancel');
                cancel.removeAttr('type');
                $('#cancel_logo').addClass('fa-remove').removeClass('fa-check');
                $('#make_live').attr('hidden', 'hidden')
            }

            $('[name="genebutton"]').each(function (i, obj) {
                if ($(obj).attr('data-name') == gene_name && $(obj).hasClass('btn-warning')) {

                    $(obj).children('.glyphicon-pencil').removeClass('glyphicon-pencil').addClass('glyphicon-ok').blur();
                    $(obj).removeClass('btn-warning').addClass('btn-success').blur();
                }
            });

            if (count_genes() == 0) {
                $('#add-all').attr('disabled', 'disabled')
            }
            else if ($('#add-all').attr('disabled') == 'disabled') {
                $('#add-all').removeAttr('disabled')
            }

            $('#regions').children().remove();
        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }

    });
}

$(document).ready(function () {
    $("#dialog").dialog({autoOpen: false});
});

function add_gene(i, gene_list, complete, progress) {
    console.log('hello');
    var total = $(gene_list).length;
    var button = $('[data-id="' + gene_list[i] + '"');
    var gene_name = $(button).attr('data-name');
    console.log(gene_name);
    var pref_tx_id = $('#' + gene_name).val();
    console.log(pref_tx_id);
    var dict = {
        "gene_id": gene_list[i],
        "panel_id": $('#main').attr('name'),
        "gene_name": gene_name,
        "tx_id": pref_tx_id
    };
    var data = JSON.stringify(dict);

    $.ajax({
        type: "POST",
        url: Flask.url_for('panels.add_all_regions'),
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function (response) {
            var gene = response["genes"];
            $('.btngene').each(function (i, obj) {
                if ($(obj).attr('data-id') == gene) {
                    $(obj).removeClass('btn-danger').addClass('btn-success');
                    $(obj).children().eq(0).removeClass('glyphicon-pencil').addClass('glyphicon-ok');
                }
            });

            complete += 1;
            progress = complete / total * 100;
            var progress_bar = $('.progress-bar');
            progress_bar.attr("aria-valuenow", progress);
            progress_bar.attr("style", "height:25px; width:" + progress.toString() + "%");
            if (i == total - 1) {
                $('#dialog').dialog("destroy");
            }
            if (!$('#cancel').hasClass('btn-success')) {
                region_added()
            }

            if (count_genes() == 0) {
                $('#add-all').attr('disabled', 'disabled');
                $('#all-genes-progress').attr('hidden', 'hidden');
            }
            else if ($('#add-all').attr('disabled') == 'disabled') {
                $('#add-all').removeAttr('disabled')
            }

            i++;
            if (i != total) {
                add_gene(i, gene_list, complete, progress)
            }

        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }
    })
}

$(document).on('click', '#add-all', function () {
    var gene_list = [];
    $("#all-genes-progress").removeAttr("hidden");
    $('.btngene').each(function (i, obj) {
        if ($(obj).children().eq(0).hasClass('glyphicon-pencil')) {
            gene_list.push($(obj).attr('data-id'))
        }
    });
    console.log('add all');
    add_gene(0, gene_list, 0, 0.0)
});

function add_gene_vp(i, gene_list, complete, progress) {
    var total = $(gene_list).length;
    var dict = {
        "gene_id": gene_list[i],
        "vpanel_id": $('#main').attr('name'),
        "panel_id": $('#panel').val()
    };
    var data = JSON.stringify(dict);

    $.ajax({
        type: "POST",
        url: Flask.url_for('panels.add_all_regions_vp'),
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function (response) {
            var gene = response["genes"];
            $('.btngene').each(function (i, obj) {
                if ($(obj).attr('data-id') == gene) {
                    $(obj).removeClass('btn-danger').addClass('btn-success');
                    $(obj).children().eq(0).removeClass('glyphicon-pencil').addClass('glyphicon-ok');
                }
            });

            complete += 1;
            progress = complete / total * 100;
            var progress_bar = $('.progress-bar');
            progress_bar.attr("aria-valuenow", progress);
            progress_bar.attr("style", "height:25px; width:" + progress.toString() + "%");
            if (i == total - 1) {
                $('#dialog').dialog("destroy");
            }
            if (!$('#cancel').hasClass('btn-success')) {
                region_added()
            }

            if (count_genes() == 0) {
                $('#add-all-vp').attr('disabled', 'disabled');
                $('#all-genes-progress').attr('hidden', 'hidden');
            }
            else if ($('#add-all').attr('disabled') == 'disabled') {
                $('#add-all').removeAttr('disabled')
            }

            i++;
            if (i != total) {
                add_gene_vp(i, gene_list, complete, progress)
            }

        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }
    })
}

$(document).on('click', '#add-all-vp', function () {
    var gene_list = [];
    $("#all-genes-progress").removeAttr("hidden");
    $('.btngene').each(function (i, obj) {
        if ($(obj).children().eq(0).hasClass('glyphicon-pencil')) {
            gene_list.push($(obj).attr('data-id'))
        }
    });

    add_gene_vp(0, gene_list, 0, 0.0)
});

function add_regions(vpanel_id, ids, geneName) {
    var dict = {
        "vp_id": vpanel_id,
        "ids": ids
    };
    var data = JSON.stringify(dict);
    $.ajax({
        type: "POST",
        url: Flask.url_for('panels.add_vp_regions'),
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function () {
            $('[name="genebutton"]').each(function (i, obj) {
                if ($(obj).attr('data-name') == geneName) {
                    $(obj).children('.glyphicon-pencil').removeClass('glyphicon-pencil').addClass('glyphicon-ok').blur();
                    $(obj).removeClass('btn-warning').addClass('btn-success').blur();
                }
            });
            $('#regions').children().remove();

            if (geneName != "Custom") {
                $('#' + geneName).attr('disabled', 'disabled');
                var label = $('[for=' + geneName + ']');
                label.attr('disabled', 'disabled');
                label.removeClass('label-success').addClass('label-added');
            }

            if ($('#cancel').hasClass('btn-danger')) {
                region_added();
            }
        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }

    });
}

function add_panel_regions(panel_id, ids, gene_name) {
    var pref_tx_id = $('#' + gene_name).val();

    var id_ext = [];
    for (var id in ids) {
        //this gets the second parent of the switch (tr)
        var row = $('[for="' + ids[id] + '"]').parent().parent();
        //this get the third child (index 2) of the row and the child of that row is the text box
        //id is original start, value is textbox start so difference is the extension
        var start = $($($($(row[0])).children().eq(2)[0])[0]).children().eq(0).attr('id');
        var ext_5 = start - $($($($(row[0])).children().eq(2)[0])[0]).children().eq(0).val();

        var end = $($($($(row[0])).children().eq(3)[0])[0]).children().eq(0).attr('id');
        var ext_3 = $($($($(row[0])).children().eq(3)[0])[0]).children().eq(0).val() - end;

        id_ext.push({"id": ids[id], "ext_5": ext_5, "ext_3": ext_3})
    }

    var dict = {
        "panel_id": panel_id,
        "id_ext": id_ext,
        "pref_tx_id": pref_tx_id,
        "project_id": $('#project').val(),
        "gene_name": gene_name
    };
    var data = JSON.stringify(dict);
    $.ajax({
        type: "POST",
        url: Flask.url_for('panels.add_panel_regions'),
        data: data,
        dataType: "json",
        contentType: "application/json",
        success: function () {
            $('[name="genebutton"]').each(function (i, obj) {
                if ($(obj).attr('data-name') == gene_name) {
                    $(obj).children('.glyphicon-pencil').removeClass('glyphicon-pencil').addClass('glyphicon-ok').blur();
                    $(obj).removeClass('btn-warning').addClass('btn-success').blur();
                }
            });
            $('#regions').children().remove();

            if (gene_name != "Custom") {
                $('#' + gene_name).attr('disabled', 'disabled');
            }

            if ($('#cancel').hasClass('btn-danger')) {
                region_added();
            }

            if (count_genes() == 0) {
                $('#add-all').attr('disabled', 'disabled')
            }
            else if ($('#add-all').attr('disabled') == 'disabled') {
                $('#add-all').removeAttr('disabled')
            }
        },
        error: function (xhr, status, error) {
            return ajax_error(xhr, status, error)
        }

    });
}

$(document).on('click', '#upload', function () {
    var file = ($('#my-file-selector'))[0].files[0];
    if (file) {
        var upload = $('#upload');
        upload.empty();
        upload.append(loading_Wheel_spin);
        // upload.load(Flask.url_for('panels.loading_wheel_spin'));
        var reader = new FileReader();
        var project_id = $('#project').val();
        var exists = "";
        reader.readAsText(file, "UTF-8");
        reader.onload = function (evt) {
            var gene_list = [];
            var current_list = [];
            $('[name="genebutton"]').each(function (j, obj) {
                current_list.push($(obj).attr('data-name'))
            });
            var lst = evt.target.result.split('\n');
            $.each(lst, function (i) {
                if ($.inArray(lst[i].replace('\r', ''), current_list) < 0) {
                    gene_list.push(lst[i].replace(/\r/g, ''))
                }
                else {
                    if (exists == "") {
                        exists += lst[i].replace(/\r/g, '')
                    }
                    else {
                        exists += ', ' + lst[i].replace(/\r/g, '')
                    }
                }
            });
            var dict = {
                "project_id": project_id,
                "gene_list": gene_list
            };

            var data = JSON.stringify(dict);
            $.ajax({
                type: "POST",
                url: Flask.url_for('panels.upload_multiple'),
                data: data,
                dataType: "json",
                contentType: "application/json",
                success: function (response) {
                    var gene_message = $('#genemessage');
                    $('[name="message-fade"]').each(function (i, obj) {
                        $(obj).remove()
                    });
                    $('#message-fail').each(function (i, obj) {
                        $(obj).remove()
                    });
                    if (exists != "") {
                        gene_message.load(Flask.url_for('panels.added_message') + "?method=multiple&gene=" + encodeURIComponent(exists));
                    }
                    gene_message.append(response['message']);

                    $('#tx_table').append(response['html']);
                    $('#genelist').append(response['button_list']);
                    if (count_genes() == 0) {
                        $('#add-all').attr('disabled', 'disabled')
                    }
                    else if ($('#add-all').attr('disabled') == 'disabled') {
                        $('#add-all').removeAttr('disabled')
                    }

                    upload.empty();
                    upload.append('Upload');
                },
                error: function (xhr, status, error) {
                    return ajax_error(xhr, status, error)
                }
            })

        };
        reader.onerror = function (xhr, status, error) {
            var trace = $('#trace');
            trace.children().remove();
            trace.append("<p>" + error + "</p>");
            $('#ajaxModal').modal('show');
            return false;
        }
    }
});

$(document).on('click', "#add-regions", function () {
    var add_Regions = $('#add-regions');
    var geneName = add_Regions.attr('name');
    var ids = count_ids();
    var vpanel_id = $('#main').attr('name');
    console.log('hello');
    console.log(ids);
    if (ids.length == 0) {
    }
    else if (add_Regions.text() == "Add Regions") {
        console.log('adding');
        if ($('#vpanelname').length) {
            add_regions(vpanel_id, ids, geneName)
        }
        else {
            add_panel_regions(vpanel_id, ids, geneName)
        }
    }
    else {
        console.log('updating');
        var to_add = [];
        var to_remove = [];

        $('.label-region').each(function (i, obj) {
            console.log('new label');
            console.log($.inArray(parseInt($(obj).attr("for")), JSON.parse(sessionStorage.getItem("current_ids"))) == -1);
            var check = $(obj).parent().children().eq(0);
            console.log($(check).prop('checked'));
            console.log($(check));

            if ($.inArray(parseInt($(obj).attr("for")), JSON.parse(sessionStorage.getItem("current_ids"))) > -1 && !$(check).prop('checked')) {
                to_remove.push($(obj).attr("for"))
            }
            else if ($.inArray(parseInt($(obj).attr("for")), JSON.parse(sessionStorage.getItem("current_ids"))) == -1 && $(check).prop('checked')) {
                to_add.push($(obj).attr("for"))
            }

        });

        console.log(to_add);
        console.log(to_remove);

        if ($('#vpanelname').length) {
            if (to_add.length > 0) {
                add_regions(vpanel_id, to_add, geneName)
            }

            if (to_remove.length > 0) {
                remove_vp_regions(vpanel_id, to_remove, geneName)
            }
        }
        else {
            if (to_add.length > 0) {
                add_panel_regions(vpanel_id, to_add, geneName)
            }

            if (to_remove.length > 0) {
                remove_panel_regions(vpanel_id, to_remove, geneName)
            }
        }
    }

});

$(document).ready(function () {

    setTimeout(function () {
        $('#message-fade').fadeOut('slow');
    }, 2000); // <-- time in milliseconds

    $('[data-toggle="tooltip"]').tooltip();

    $("#genelabels").hide();

    function add_panel_gene() {
        var project_id = $('#project').val();
        var gene_name = $('#genes').val();

        if ($('#' + gene_name).length) {
            $('#genemessage').load(Flask.url_for('panels.added_message') + "?type=single&gene=" + gene_name);
            return
        }

        if (gene_name.length != 0) {
            var dict = {
                "project_id": project_id,
                "gene_name": gene_name
            };

            var data = JSON.stringify(dict);


            $.ajax({
                type: "POST",
                url: Flask.url_for('panels.create_panel_get_tx'),
                data: data,
                dataType: "json",
                contentType: "application/json",
                success: function (response) {
                    $('[name="message-fade"]').each(function (i, obj) {
                        $(obj).remove()
                    });
                    $('[name="message-fail"]').each(function (i, obj) {
                        $(obj).remove()
                    });
                    $('#genemessage').append(response['message']);
                    $('#tx_table').append(response['html']);
                    $('#genelist').append(response['button_list']);
                    if (count_genes() == 0) {
                        $('#add-all').attr('disabled', 'disabled')
                    }
                    else if ($('#add-all').attr('disabled') == 'disabled') {
                        $('#add-all').removeAttr('disabled')
                    }
                    var add = $('#add');
                    add.empty();
                    add.append('Add');
                    $('#genes').val('');
                },
                error: function (xhr, status, error) {
                    return ajax_error(xhr, status, error)
                }
            })
        }
    }

    $("#add").click(function () {
        if ($('#genes').val().length > 0) {
            var add = $('#add');
            add.empty();
            add.append(loading_Wheel_spin);
            // add.load(Flask.url_for('panels.loading_wheel_spin'));
            add_panel_gene()
        }
    });
});

$(function () {
    $("#genes").autocomplete({
        source: function (request, response) {
            $.getJSON(Flask.url_for('panels.autocomplete'), {
                q: request.term // in flask, "q" will be the argument to look for using request.args
            }, function (data) {
                response(data.matching_results); // matching_results from jsonify
            });
        },
        minLength: 2,
        select: function (event, ui) {
            console.log(ui.item.value); // not in your question, but might help later
        }
    });
});

function get_length() {
    if ($('#tables').val() == "Transcript") {
        return 5
    }
    else {
        return 2
    }
}

$(function () {
    $("#search_term").autocomplete({
        source: function (request, response) {
            var url = '';
            var value = $('#tables').val();
            if (value == "Genes") {
                url = Flask.url_for('panels.autocomplete')
            }
            else if (value == "Transcripts") {
                url = Flask.url_for('search.autocomplete_tx');
            }
            else if (value == "Panels") {
                url = Flask.url_for('search.autocomplete_panel')
            }
            else if (value == "VPanels") {
                url = Flask.url_for('search.autocomplete_vp')
            }
            else if (value == "Projects") {
                url = Flask.url_for('search.autocomplete_project')
            }
            else if (value == "Users") {
                url = Flask.url_for('search.autocomplete_user')
            }

            $.getJSON(url, {
                q: request.term // in flask, "q" will be the argument to look for using request.args
            }, function (data) {
                response(data.matching_results); // matching_results from jsonify
            });
        },
        minLength: get_length(),
        select: function (event, ui) {
            console.log(ui.item.value); // not in your question, but might help later
        }
    });
});
