from django.contrib import admin
from .models import *
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'useremail', 'last_logon','user_is_active')

class TeamAdmin(admin.ModelAdmin):
    list_display = ('teamname','teamemail','created_on','is_active')

class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('handoverid','createdby','discussiontime')

class ChangestableAdmin(admin.ModelAdmin):
    list_display = ('changedon','handover','changedby','changecomment')

class ChangetypeAdmin(admin.ModelAdmin):
    list_display = ('changetypename','changetypeweight')

class ConfigAdmin(admin.ModelAdmin):
    list_display = ('configname','configvalue')

class TeammemberAdmin(admin.ModelAdmin):
    list_display = ('team','user','is_approved')

class HandoverAdmin(admin.ModelAdmin):
    list_display = ('title','createdby','status')

class LogsAdmin(admin.ModelAdmin):
    list_display = ('logcomment','logged_by','related_user','related_team')

admin.site.register(User, UserAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Discussion, DiscussionAdmin)
admin.site.register(Changestable, ChangestableAdmin)
admin.site.register(Changetype, ChangetypeAdmin)
admin.site.register(ConfigurationValue, ConfigAdmin)
admin.site.register(Teammember,TeammemberAdmin)
admin.site.register(Handover, HandoverAdmin)
admin.site.register(Logs,LogsAdmin)
admin.site.register(Attachments)