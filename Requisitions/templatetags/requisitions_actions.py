from django import template
from django.contrib import admin

register = template.Library()


@register.inclusion_tag('admin/requisitions/submit_line_with_actions.html', takes_context=True)
def actions_row(context):
    """
    Displays the row of buttons for delete and save.
    """
    # import pprint
    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(context)
    print context['object_id']
    print dir(context['adminform'])
    return context

    # print admin.site.get_urls()
    # opts = context['opts']
    # change = context['change']
    # is_popup = context['is_popup']
    # save_as = context['save_as']
    # ctx = {
    #     'opts': opts,
    #     'show_delete_link': (
    #         not is_popup and context['has_delete_permission'] and
    #         change and context.get('show_delete', True)
    #     ),
    #     'show_save_as_new': not is_popup and change and save_as,
    #     'show_save_and_add_another': (
    #         context['has_add_permission'] and not is_popup and
    #         (not save_as or context['add'])
    #     ),
    #     'show_save_and_continue': not is_popup and context['has_change_permission'],
    #     'is_popup': is_popup,
    #     'show_save': True,
    #     'preserved_filters': context.get('preserved_filters'),
    # }
    # if context.get('original') is not None:
    #     ctx['original'] = context['original']
    # print ctx
    # return ctx