from django import template 

register = template.Library() 


@register.filter 
def get_attrs(value, arg): 
    return getattr(value, arg)