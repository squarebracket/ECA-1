from django.conf.urls import patterns, include, url
from django.contrib import admin
from Seller.views import some_view, get_item
from people.views import get_student, search_student

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Inventory.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^someview/$', some_view),
    url(r'^get_student/(\d{1,9})/$', get_student),
    url(r'^get_item/(\d{1,9})/$', get_item),
    url(r'^search_student/(.*)/$', search_student),
)
