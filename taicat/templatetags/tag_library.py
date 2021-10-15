# templatetags/tag_library.py
#https://stackoverflow.com/a/15820445/644070

import re

from django import template

register = template.Library()

@register.filter()
def to_int(value):
    return int(value)

@register.simple_tag()
def find_event_num(data, year, month):
    for i in data['round_list']:
        if int(i['year']) == int(year) and \
           int(i['month']) == int(month):
            return i['event_num']
    return 0

@register.filter
def off_page(value):
    match_list = [x.group() for x in re.finditer(r'&page=[0-9]*|page=[0-9]*', value)]

    for x in match_list:
        value = value.replace(x, '')
    return value

# for calculation
@register.simple_tag()
def find_oi_3(data, year, month):
    for i in data['round_list']:
        if int(i['year']) == int(year) and \
           int(i['month']) == int(month):
            if wh := i['working_hour'][0]:
                return i['image_num'] * 1.0 / wh * 1000
    return 0