/**
 * Created by chuck on 2014-09-20.
 */
$ = django.jQuery;
$(function() {
    // Insert results table into DOM
    $('#id_buyer').after('<div id="search_results" style="width: 300px; position: absolute; border: 2px solid black; background-color: white; display: none; z-index: 10;">' +
        '<table id="search_results_table" style="width: 100%;"></table>' +
        '</div>');
    $('#id_buyer').after('<div id="info"></div>')
    $('#search_results').css('left', $('#id_buyer').offset().left + $('#id_buyer').outerWidth());
    $('#search_results').css('top', $('#id_buyer').offset().top);

    // The number of results returned is used for hiding table if num_results <= 0,
    // and for auto-selecting student if num_results = 1
    var num_results = 0;
    var last_request = null;
    // object mapping request URLs -> request objects
    var requests = {};
    var last_search_query = '';


    $('#id_buyer').keyup(function() {

        if ($(this).val() == '') { return; }

        last_search_query = '/search_student/' + $('#id_buyer').val() + '/';
        console.log('request for ' + last_search_query);

        last_request = $.getJSON('/search_student/' + $('#id_buyer').val() + '/')
            .success(function(data) {
                // if it's the most recent ajax call
                if (this.url == last_search_query) {
                    // ensure no others complete after this one
                    console.log('Request for ' + this.url + 'completed: ');
                    delete requests[last_search_query];
                    for (request in requests) {
                        requests[request].abort();
                        delete requests[request];
                        console.log("Request " + request + ' aborted');
                    }
                }
                //if (data.length <= 0) { return; }
                num_results = data.length;
                // display search results table, and empty it
                $('#search_results').css('display', 'block');
                var table = $('#search_results_table');
                table.html('<tr><td>Student ID</td><td>Name</td><td>ECA ID</tr>');
                // make rows for each student result...
                $.each(data, function(index, value) {
                    data = value.fields;
                    var row = $('<tr><td class="result_sid">' + data.student_id + '</td><td class="result_name">' +
                        data.first_name + ' ' + data.last_name + '</td><td class="result_id">' + value.pk + '</td></tr>');
                    row.hover(function() {
                        $(this).css('background-color', '#ff0000');
                    },
                    function() {
                        $(this).css('background-color', '#ffffff');
                    });
                    row.mousedown(function() {
                        $('#id_buyer').val($(this).find('.result_id').html());
                    });
                    table.append($(row));
                })
//            for (x in this) {
//                current = $('#info').html();
//                $('#info').html(current + x + ' = ' + this[x] + '<br>');
//            }
            });
        requests[last_search_query] = last_request;
    });

    //// EVENT ACTION FOR BUYER FOCUSOUT
    var original_id = $('#id_buyer').val();

    $('#id_buyer').focusout(function () {
        if ($('#id_buyer').val() == '') { return; }
        // if a search returned only 1 result, automatically take it
        if (num_results == 1) {
            var id = $('#search_results_table').find('.result_id').html();
            $('#id_buyer').val(id);
        }
        // hide results table, if shown
        $('#search_results').css('display', 'none');
        // attempt to get student object
        $.getJSON('/get_student/' + $('#id_buyer').val() + '/', function (data, success_text, jqXHR) {
            original_id = data[0].pk;
            data = data[0].fields;
            $('#first_name').html(data.first_name);
            $('#last_name').html(data.last_name);
            $('#email').html(data.email);
            $('#address').html(data.address);
            $('#student_id').html(data.student_id);
        })
            .fail(function() {
                // if it fails, reset to the most recent valid one.
                alert("Student with that ID does not exist in the database.");
                $('#id_buyer').val(original_id);
                $('#search_results').css('display', 'none');
            });
    });
    $.fn.extend({
        recalculateRow: function() {
            var unit_cost = $(this).find('.field-unit_cost > p').html().substr(1);
            var qty = $(this).find('.field-quantity > input').val();
            if ((unit_cost == "None)") && (qty = '')) { return $(this).find('.field-amount > p').html('$0.00'); }
            return $(this).find('.field-amount > p').html('$' + (qty * unit_cost).toFixed(2));
        }
    });

    function recalculateReceipt() {
        var total_amount_span = $('#receipt_total');
        var total = 0.0;
        $('.dynamic-lineitem_set').each(function() {
            total = total + parseFloat($(this).find('.field-amount > p').html().substr(1));
        });
        total_amount_span.html('$' + total.toFixed(2));
        return total;
    };
    function changeItem(row) {
        var item_id = $(row).find('.field-item > select').val();
        var id = $(row).attr('id');
        var unit_cost = $('#id_' + id + '-unit_cost');
        $.getJSON('/get_item/' + item_id + '/', function (data) {
            data = data[0].fields;
            $(unit_cost).html('$' + parseFloat(data.cost).toFixed(2));
            $(row).recalculateRow();
            recalculateReceipt();
        })
    }

    $('.dynamic-lineitem_set').each(function() {
        number = $(this).attr('id').substr(-1,1);
        var amt = $(this).find('.field-amount > p');
        amt.attr('id', 'id_lineitem_set-' + number + '-amount');
        var unit_cost = $(this).find('.field-unit_cost > p');
        unit_cost.attr('id', 'id_lineitem_set-' + number + '-unit_cost');
        var qty = $(this).find('#id_lineitem_set-' + number + '-quantity');
        var item = $(this).find('#id_lineitem_set-' + number + '-item');
        var row = this;
        qty.change(function() {
            $(row).recalculateRow();
            recalculateReceipt();
        });
        item.change(function() {
            changeItem(row);
        })

    });
    $('tr.add-row').click(function(e) {
        lastRow = $('tr.add-row').prev().prev();
        number = $(lastRow).attr('id').substr(-1,1);
        var amt = $(lastRow).find('.field-amount > p');
        amt.attr('id', 'id_lineitem_set-' + number + '-amount');
        var unit_cost = $(lastRow).find('.field-unit_cost > p');
        unit_cost.attr('id', 'id_lineitem_set-' + number + '-unit_cost');
        var qty = $(lastRow).find('#id_lineitem_set-' + number + '-quantity');
        var item = $(lastRow).find('#id_lineitem_set-' + number + '-item');
        var row = lastRow;
        qty.change(function() {
            $(row).recalculateRow();
            recalculateReceipt();
        });
        item.change(function() {
            changeItem(row);
        })
    });
});
