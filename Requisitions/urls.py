from django.conf.urls import patterns, include, url
from Requisitions.views import approve

urlpatterns = patterns('',

    url(r'^admin/Requisitions/.*/(\d+)/approve/', approve),
)