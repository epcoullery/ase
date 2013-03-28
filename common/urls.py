from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView
from repart import views

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='/admin/'), name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^promotions/(?P<pk>.+)?', views.promotions),
    url(r'^teachers/charges/(?P<pk>\d*)', views.teachers_charges),
    url(r'^teachers/(?P<pk>\d+)?', views.teachers),
    url(r'^contents/(?P<pk>\d+)?', views.contents),
    url(r'^missions/$', views.missions),
    url(r'^generate', views.generate),
    url(r'^genall', views.genall),
    url(r'^remaind', views.remaind),
    url(r'^supervision/$', views.supervision),

    # Appel AJAX
    url(r'^course/(?P<pk_course>\d+)/(?P<pk_teacher>\d+)$', views.update_courses),
)
