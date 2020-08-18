from django import template
from datetime import datetime
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def paymentyears(value):
	links = "";
	year = datetime.now().year;
	links = links+'<a href="%s/%i/">%i</a>, ' % (value, year-1, year-1)
	links = links+'<a href="%s/%i/">%i</a>' % (value, year, year)
	return mark_safe(links);
