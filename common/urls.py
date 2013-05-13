from django.conf.urls.defaults import patterns, include, url
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
    url(r'^generate_cours/$', views.generate),
    url(r'^genall/$', views.genall),
    url(r'^remaind', views.remaind),
    url(r'^generate_supervision/$', views.supervision),
    url(r'^supervision/(?P<pk>.+)?', views.supervision_by_promotion),
    url(r'^global_supervision/$', views.global_supervision),
    url(r'^export_teachers/$', views.export_teachers),
    url(r'^export_controls/$', views.export_controls),
    # Appel AJAX
    url(r'^course/(?P<pk_course>\d+)/(?P<pk_teacher>\d+)$', views.update_courses),
    url(r'^supervision_add/(?P<pk>\d+)', views.supervision_add),
    url(r'^supervision_minus/(?P<pk>\d+)', views.supervision_minus),
)
