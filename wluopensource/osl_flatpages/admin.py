from django.contrib import admin

from osl_flatpages.models import Flatpage

class FlatpageAdmin(admin.ModelAdmin):
    pass
admin.site.register(Flatpage, FlatpageAdmin)

