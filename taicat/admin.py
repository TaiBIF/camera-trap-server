import csv
from django.contrib import admin
from django.http import HttpResponse

from .models import (
    Project,
    StudyArea,
    Deployment,
    Organization,
    Contact,
    ProjectMember,
    Image,
    ParameterCode,
    DownloadLog,
)

class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"
    
@admin.register(ProjectMember)
class ProjectAdmin(admin.ModelAdmin):
    model = ProjectMember


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    model = Organization

    filter_horizontal = ('projects',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    model = Contact

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    model = Project

    #filter_horizontal = ('members',)

@admin.register(StudyArea)
class StudyAreaAdmin(admin.ModelAdmin):
    model = StudyArea
    list_display = ('name', 'project')

@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    model = Deployment
    list_display = ('name', 'project', 'study_area')

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    model = Image
    list_filter = ('deployment', 'memo')
    list_display = ('filename', 'datetime', 'created', 'deployment', 'memo')
    search_fields = ('filename', )

@admin.register(ParameterCode)
class ParameterCodeAdmin(admin.ModelAdmin):
    model = ParameterCode
    list_display = ('name', 'type')
    

@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin,ExportCsvMixin):
    model = DownloadLog
    list_display = ('user_role', 'condition','file_link')
    actions = ["export_as_csv"]