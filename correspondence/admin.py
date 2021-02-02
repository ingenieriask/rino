from django.contrib import admin
from correspondence.models import State,City,Radicate,UserProfileInfo,Office,Person

# Register your models here.
admin.site.register(State)
admin.site.register(City)
# admin.site.register(Radicate)
admin.site.register(UserProfileInfo)
admin.site.register(Office)
admin.site.register(Person)

@admin.register(Radicate)
class RadicateAdmin(admin.ModelAdmin):
    list_display = ('number','date_radicated','subject')
    list_filter = ('type','reception_mode','person','creator')
    search_fields = ('subject','number')
    ordering = ('-date_radicated',)
    date_hierarchy = 'date_radicated'
    raw_id_fields = ('person','creator')
