from django import template
from QB.qb2 import lower_case_to_camel_case


register = template.Library()


class Something(template.Node):
    def __init__(self, argument):
        self.argument = argument

    def render(self, context):
        if self.argument in context:
            if 'list_id' in context[self.argument]:
                string = '<ListID>%s</ListID>' % lower_case_to_camel_case(context[self.argument].list_id)
            elif 'full_name' in context[self.argument]:
                string = '<FullName>%s</FullName>' % lower_case_to_camel_case(context[self.argument].full_name)
            else:
                raise Exception('Ref does not have list_id or full_name')
            tag = lower_case_to_camel_case(self.argument)
            return '<%s>%s</%s>' % (tag, string, tag)
        else:
            return ''

@register.tag
def qb_ref(parser, tag_stuff):
    try:
        tag_name, argument = tag_stuff.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % tag_stuff.contents.split()[0])
    print 'argument is', argument
    return Something(argument)