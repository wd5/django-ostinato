from django.contrib import admin
from django.contrib.admin.util import unquote

from mptt.admin import MPTTModelAdmin

from ostinato.statemachine.forms import StateMachineModelForm
from ostinato.pages.models import Page, DefaultStateMachine
from ostinato.pages.utils import get_zones_for


def inline_factory(zone_instance, page):

    class ZoneInline(admin.StackedInline):
        model = zone_instance.__class__
        exclude = ('zone_id',)
        extra = 0
        max_num = 1
        can_delete = False

        def queryset(self, request):
            qs = super(ZoneInline, self).queryset(request)
            return qs.filter(zone_id=zone_instance.zone_id, page=page).distinct()

    return ZoneInline


class PageAdminForm(StateMachineModelForm):

    class Meta:
        model = Page


## Admin Models
class PageAdmin(MPTTModelAdmin):
    form = PageAdminForm

    list_display = ('title', 'slug', 'template', 'author', 'state',
        'show_in_nav', 'show_in_sitemap', 'created_date', 'modified_date',
        'publish_date')
    list_filter = ('template', 'author', 'show_in_nav', 'show_in_sitemap',
        '_sm__state')
    search_fields = ('title', 'short_title', 'slug', 'author')
    date_hierarchy = 'publish_date'

    fieldsets = (
        (None, {
            'fields': (
                ('title', 'short_title', 'slug'),
                'template', 'redirect', 'parent',
                ('show_in_nav', 'show_in_sitemap'),
            ),
        }),

        ('Publication', {
            'fields': ('author', 'publish_date', '_sm_action'),
        }),

    )
    prepopulated_fields = {'slug': ('title',)}


    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        We need to dynamically create the inline models since it
        changes based on the template.
        """
        page = self.get_object(request, unquote(object_id))

        inlines = []

        if page is not None:
            for zone in get_zones_for(page):
                inlines.append(inline_factory(zone, page))

        # Note: doing self.inlines.append(inlines) will cause a bug where 
        # the same zones will show multiple times.
        self.inlines = inlines

        return super(PageAdmin, self).change_view(
            request, object_id, form_url='', extra_context=None)


admin.site.register(Page, PageAdmin)
