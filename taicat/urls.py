from django.urls import path
from . import (
    views,
    search_view
)
from .views import robots_txt


urlpatterns = [
    path('project/overview', views.project_overview, name='project_overview'),
    path('project/info/<pk>/', views.project_info, name='project_info'),
    path('project/create', views.create_project, name='create_project'),
    path('project/edit/basic/<pk>/', views.edit_project_basic, name='edit_project_basic'),
    path('project/edit/deployment/<pk>/', views.edit_project_deployment, name='edit_project_deployment'),
    path('project/edit/members/<pk>/', views.edit_project_members, name='edit_project_members'),
    path('project/edit/license/<pk>/', views.edit_project_license, name='edit_project_license'),
    path('project/details/<pk>/', views.project_detail, name='project_detail'),
    path('project/oversight/<pk>/', views.project_oversight, name='project_oversight'),
    path('project/oversight/<pk>/download/', views.download_project_oversight, name='download_project_oversight'),
    path('api/project/remarks/<pk>/', views.project_remarks, name='project_remarks'),
    path('api/deployment_journals/<pk>/', views.api_update_deployment_journals, name='update-deployment-journals'),
    path('api/deployment_journals/', views.api_create_or_list_deployment_journals, name='create-deployment-journals'),
    # path('api/check_data_gap/', views.api_check_data_gap, name='check-data-gap'),
    path('api/data', views.data, name='data'),
    # path('api/update_datatable', views.update_datatable, name='update_datatable'),
    path('api/deployment/', views.get_deployment, name='deployment'),
    path('api/add_studyarea', views.add_studyarea, name='add_studyarea'),
    path('api/add_deployment', views.add_deployment, name='add_deployment'),
    path('api/edit_image/<pk>', views.edit_image, name='edit_image'),
    path('api/get_edit_info/', views.get_edit_info, name='get_edit_info'),
    path('api/get_project_detail/', views.get_project_detail, name='get_project_detail'),
    path('api/get_project_info_web/', views.get_project_info_web, name='get_project_info_web'),
    path('api/get_gap_choice/', views.get_gap_choice, name='get_gap_choice'),
    path('api/get_parameter_name/', views.get_parameter_name, name='get_parameter_name'),
    path('api/check_login/', views.check_login, name='check_login'),
    path('api/project/overview', views.get_project_overview, name='get_project_overview'),
    path('download/<pk>', views.download_request, name='download'),
    path('api/add/members/<pk>/', views.add_project_members, name='add_project_members'),

    path('api/get_image_info/', views.get_image_info, name='get_image_info'),
    path('update_line_chart/', views.update_line_chart, name='update_line_chart'),

    #    path('download/data/<uidb64>/<token>', views.download_data, name='download_data'),
    path('search/', search_view.index, name='search'),
    path('api/search', search_view.api_search, name='get_search'),
    path('api/species', search_view.api_get_species, name='get_species'),
    path('api/projects', search_view.api_get_projects, name='get_projects'),
    path('api/deployments', search_view.api_deployments, name='get_deployments'),
    path('api/named_areas/', search_view.api_named_areas, name='get_named_areas'),
    path('delete/<pk>/', views.delete_data, name='delete_data'),
    path('get_sa_points', views.get_sa_points, name='get_sa_points'),
    path('get_subsa', views.get_subsa, name='get_subsa'),
    path('update_species_pie', views.update_species_pie, name='update_species_pie'),
    path('delete_dep_sa', views.delete_dep_sa, name='delete_dep_sa'),
    path('edit_sa', views.edit_sa, name='edit_sa'),
    path('update_species_map', views.update_species_map, name='update_species_map'),
    path('update_edit_autocomplete', views.update_edit_autocomplete, name='update_edit_autocomplete'),
    path('delete_project', views.delete_project, name='delete_project'),
    
    path("robots.txt", robots_txt),
]
