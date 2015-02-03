from django.conf.urls import patterns, include, url
from django.contrib import admin
from Seller.views import some_view, get_item
from people.views import get_student, search_student, get_person, search_person
from django.views.generic.base import RedirectView
from Seller.views import export

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Inventory.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^someview/$', some_view),
    url(r'^get_student/(\d{1,9})/$', get_student),
    url(r'^get_person/(\d{1,9})/', get_person),
    url(r'^get_item/(\d{1,9})/$', get_item),
    url(r'^search_student/(.*)/$', search_student),
    url(r'^search_person/(.*)/$', search_person),
    url(r'^export/$', export),
    url(r'^qb/', include('QB.urls', namespace='qb')),
    url(r'^core/', include('core.urls', namespace='core')),
    url(r'', include('Requisitions.urls', namespace='Requisitions')),
    url('', include('social.apps.django_app.urls', namespace='social')),
)
