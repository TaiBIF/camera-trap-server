from django.urls import path

from . import client_views

urlpatterns = [
    #path('', views.index, name='index'),
    path('projects/', client_views.get_project_list, name='get-project-list'),
    path('projects/<int:project_id>/', client_views.get_project, name='get-project'),
    path('image/annotation/', client_views.post_image_annotation, name='post-image-annotation'),
    path('image/update/', client_views.update_image, name='update-image'),
    path('check_deployment_journal_upload_status/<pk>/', client_views.check_deployment_journal_upload_status, name='check-deployment-journal-upload-status'),
    path('check_update/<version>/', client_views.check_update, name='check-update'),
    path('check_folder/<name>/', client_views.check_folder, name='check-folder'),
    path('user_info/<int:user_id>', client_views.get_user_info, name='get-user-info'),
]
