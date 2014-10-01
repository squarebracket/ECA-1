/**
 * Created by chuck on 2014-09-20.
 */
$ = django.jQuery;
$(function() {
    var original_id = $('#id_buyer').val();
    $('#id_buyer').focusout(function () {
        $.getJSON('/get_student/' + $('#id_buyer').val() + '/', function (data, success_text, jqXHR) {
            original_id = data[0].pk;
            data = data[0].fields;
            $('#first_name').html(data.first_name);
            $('#last_name').html(data.last_name);
            $('#email').html(data.email);
            $('#address').html(data.address);
        })
            .fail(function() {
                alert("Student with that ID does not exist in the database.");
                $('#id_buyer').val(original_id);
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
