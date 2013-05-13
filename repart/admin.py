# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin

from repart.models import (Teacher, Promotion, Content, Formation, TheoricStudiesPlan, AppliedStudiesPlan,
                           AdminContent, AdminJob, Supervision, Todo)

class AdminJobInLines(admin.TabularInline):
    model = AdminJob
    extra = 0

class TeacherAdmin(admin.ModelAdmin):
    inlines = [AdminJobInLines]

class AdminCoursesInLines(admin.TabularInline):
    model=AppliedStudiesPlan
    extra=0


admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Promotion)
admin.site.register(Content)
admin.site.register(Formation)
admin.site.register(TheoricStudiesPlan)
admin.site.register(AdminContent)
admin.site.register(AppliedStudiesPlan)
admin.site.register(AdminJob)
admin.site.register(Supervision)
admin.site.register(Todo)