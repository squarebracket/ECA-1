$ = django.jQuery;

var original_id = '';

var tax_rates;
$.getJSON('/core/tax_rates/')
    .success(function(data) {
        tax_rates = data;
    });

// The number of results returned is used for hiding table if num_results <= 0,
// and for auto-selecting student if num_results = 1
var num_results = 0;
var last_request = null;
// object mapping request URLs -> request objects
var requests = {};
var last_search_query = '';

$(function() {

    // Insert results table into DOM
    $('#id_searcher').after('<div id="search_results" style="width: 300px; position: absolute; border: 2px solid black; background-color: white; display: none; z-index: 10;">' +
        '<table id="search_results_table" style="width: 100%;"></table>' +
        '</div>');
    $('#id_searcher').after('<div id="info"></div>')
    $('#search_results').css('left', $('#id_searcher').offset().left + $('#id_searcher').outerWidth());
    $('#search_results').css('top', $('#id_searcher').offset().top);


    $('#id_searcher').keyup(function() {

        if ($(this).val() == '') { return; }

        last_search_query = '/search_person/' + $('#id_searcher').val() + '/';
        console.log('request for ' + last_search_query);

        last_request = $.getJSON('/search_person/' + $('#id_searcher').val() + '/')
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
                $.each(data, function(index, data) {
                    var row = $('<tr><td class="result_sid">' + data.student_id + '</td><td class="result_name">' +
                        data.full_name + '</td><td class="result_id">' + data.pk + '</td></tr>');
                    row.hover(function() {
                        $(this).css('background-color', '#ff0000');
                    },
                    function() {
                        $(this).css('background-color', '#ffffff');
                    });
                    row.mousedown(function() {
                        $('#id_payee').val($(this).find('.result_id').html());
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

    //// EVENT ACTION FOR payee FOCUSOUT
    original_id = $('#id_payee').val();

    $('#id_searcher').focusout(function () {
        if ($('#id_searcher').val() == '') { return; }
        // if a search returned only 1 result, automatically take it
        if (num_results == 1) {
            var id = $('#search_results_table').find('.result_id').html();
            $('#id_payee').val(id);
        }
        // hide results table, if shown
        $('#search_results').css('display', 'none');
        $('#id_searcher').val('');
        // attempt to get student object
        get_person_data();
    });
    $.fn.extend({
        recalculateRow: function() {
            var amount = $(this).find('.field-_amount_entered > input').val();
            var tax_id = $(this).find('.field-tax_code > select').val();
            var tax_in = $(this).find('.field-tax_included > input').val();
            if (tax_in == true) {
                var amount_with_tax = amount;
            }
            else {
                var amount_with_tax = amount * (1 + (tax_id != '' ? tax_rates[tax_id] : 0));
            }
            console.log(amount_with_tax);
            return $(this).find('.field-amount_with_tax > p').html('$' + (amount_with_tax).toFixed(2));
        }
    });

    var payee = $('#id_payee').val();
    if (payee != '') {
        get_person_data();
        recalculateReceipt();
    }

    $('.dynamic-reqlineitem_set').each(function() {
        setup_row_events(this);
    });

    $('tr.add-row').click(function(e) {
        var lastRow = $('tr.add-row').prev().prev();
        setup_row_events(lastRow);
    });
});

function set_payee_data(payee, success_text, jqXHR) {
    original_id = payee.pk;
    $('#first_name').html(payee.first_name);
    $('#last_name').html(payee.last_name);
    $('#email').html(payee.email);
    $('#address').html(payee.address);
    $('#student_id').html(payee.student_id);
}

function get_person_data() {
    $.getJSON('/get_person/' + $('#id_payee').val() + '/', set_payee_data)
        .fail(function() {
            // if it fails, reset to the most recent valid one.
            alert("Student with that ID does not exist in the database.");
            $('#id_payee').val(original_id);
            $('#search_results').css('display', 'none');
        });
}

function recalculateReceipt() {
    var total_amount_span = $('.field-total > div > p');
    var total = 0.0;
    $('.dynamic-reqlineitem_set').each(function() {
        total = total + parseFloat($(this).find('.field-amount_with_tax > p').html().substr(1));
    });
    total_amount_span.html('$' + total.toFixed(2));
    $('#id_total_amount').val(total);
    return total;
};

function setup_row_events(row) {
    var number = $(row).attr('id').substr(-1,1);
    var amt = $(row).find('.field-_amount_entered > input');
    amt.attr('id', 'id_reqlineitem_set-' + number + '-_amount_entered');
    var tax_in = $(row).find('.field-tax_included > input');
    tax_in.attr('id', 'id_reqlineitem_set-' + number + '-tax_in');
    var tax_code = $(row).find('#id_reqlineitem_set-' + number + '-tax_code');
    amt.add(tax_code).add(tax_in).change(function() {
        $(row).recalculateRow();
        recalculateReceipt();
    });
}