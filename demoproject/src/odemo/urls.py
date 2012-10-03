from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import DetailView

from ostinato.pages.registry import page_content
from ostinato.pages.sitemaps import PageSitemap
from odemo.news.models import NewsItem


admin.autodiscover()
page_content.autodiscover()


sitemaps = {
    'pages': PageSitemap,
}

urlpatterns = patterns('',
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': sitemaps}),
    
    (r'^ckeditor/', include('ckeditor.urls')),
    
    url(r'^admin/', include(admin.site.urls)),
    (r'^grappelli/', include('grappelli.urls')),
)

urlpatterns += staticfiles_urlpatterns()

urlpatterns += patterns('', url(r'^', include('ostinato.pages.urls')), )
