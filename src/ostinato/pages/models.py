import re

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.conf import settings

from mptt.models import MPTTModel, TreeForeignKey
from mptt.managers import TreeManager

from ostinato.pages.managers import PageManager


TEMPLATE_CHOICES = getattr(settings, 'OSTINATO_PAGE_TEMPLATES')
DEFAULT_STATE = getattr(settings, 'OSTINATO_PAGES_DEFAULT_STATE', 5)


## Models
class Page(MPTTModel):
    """ A basic page model """
    PRIVATE = 0
    PUBLISHED = 5
    ARCHIVED = 10
    STATE_CHOICES = (
        (PRIVATE, 'Private'),
        (PUBLISHED, 'Published'),
        (ARCHIVED, 'Archived'),
    )

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, help_text='A url friendly slug.')
    short_title = models.CharField(max_length=15, null=True, blank=True,
        help_text='A shorter title which can be used in menus etc. If this \
                   is not supplied then the normal title field will be used.')

    template = models.CharField(max_length=100, choices=TEMPLATE_CHOICES)

    redirect = models.CharField(max_length=200, blank=True, null=True,
        help_text='Use this to point to redirect to another page or website.')

    show_in_nav = models.BooleanField(default=True)
    show_in_sitemap = models.BooleanField(default=True)

    state = models.IntegerField(choices=STATE_CHOICES, default=DEFAULT_STATE)

    created_date = models.DateTimeField(null=True, blank=True)
    modified_date = models.DateTimeField(null=True, blank=True)
    publish_date = models.DateTimeField(null=True, blank=True)

    author = models.ForeignKey(User, related_name='pages_authored',
        null=True, blank=True)

    parent = TreeForeignKey('self', null=True, blank=True,
        related_name='page_children') 

    ## Managers
    objects = PageManager()
    tree = TreeManager()

    ## required for caching contents
    _contents = None

    def __unicode__(self):
        return '%s' % self.title


    def save(self, *args, **kwargs):
        ## Publishing
        now = timezone.now()

        if not self.id or not self.created_date:
            self.created_date = now

        if self.state == Page.PUBLISHED and not self.publish_date:
            self.publish_date = now

        self.modified_date = now

        super(Page, self).save(*args, **kwargs)


    def get_short_title(self):
        if self.short_title:
            return self.short_title
        else:
            return self.title


    @models.permalink
    def perma_url(self, data):
        """ A seperate method to specifically deal with permalinks """
        return data


    def get_absolute_url(self):
        """ Cycle through the parents and generate the path """

        if self.redirect:
            return self.redirect

        if self == Page.tree.root_nodes()[0]:
            return reverse('ostinato_page_home')

        path = []
        for parent in self.get_ancestors():
            path.append(parent.slug)

        path.append(self.slug)

        return self.perma_url(
            ('ostinato_page_view', None, {'path': '/'.join(path)}) )


    def get_content_model(self):
        label, model = self.template.split('.')
        content_type = ContentType.objects.get(app_label=label, model=model)
        return content_type.model_class()


    def get_content(self):
        if not self._contents:
            label, model = self.template.split('.')
            content_type = ContentType.objects.get(app_label=label, model=model)
            self._contents = content_type.get_object_for_this_type(page=self.id)

        return self._contents

    contents = property(get_content)


    def get_template(self):
        return self.get_content_model().get_template()


## Page Templates
class PageContent(models.Model):
    """
    Our base PageContent model. All other content models need to subclass
    this one.
    """

    page = models.OneToOneField(Page,
        related_name='%(app_label)s_%(class)s_content')

    class Meta:
        abstract = True

    class ContentOptions:
        """
        Custom Options for the Content
        ``template`` is the template path relative the templatedirs.
        ``view`` is a custom view that will handle the rendering for the page.
        ``form`` a custom form to use in the admin.
        """
        template = None
        view = 'ostinato.pages.views.PageView'
        form = None

    @classmethod
    def get_template(cls):
        template = getattr(cls.ContentOptions, 'template', None)

        if not template:
            cls_name = re.findall('[A-Z][^A-Z]*', cls.__name__)
            template = 'pages/%s.html' % '_'.join([i.lower() for i in cls_name])

        return template

