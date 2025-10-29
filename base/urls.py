from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout', views.logout, name='logout'),
    path('personal_info', views.personal_info, name='personal_info'),
    path('api/stat_county', views.stat_county, name='stat_county'),
    path('api/stat_studyarea', views.stat_studyarea, name='stat_studyarea'),
    path('api/get_growth_data', views.get_growth_data, name='get_growth_data'),
    path('api/get_geo_data', views.get_geo_data, name='get_geo_data'),
    path('api/get_species_data', views.get_species_data, name='get_species_data'),
    path('callback/orcid/auth/<via>', views.get_auth_callback, name='get_auth_callback'),
    # path('callback/orcid/authcode', views.get_auth_code, name='get_auth_code')
    path('test/login', views.login_for_test, name='login_for_test'),
    path('permission', views.set_permission, name='set_permission'),
    path('add_org_admin', views.add_org_admin, name='add_org_admin'),
    path('policy', views.policy, name='policy'),
    path('faq', views.faq, name='faq'),
    path('contact-us', views.contact_us, name='contact-us'),
    path('get_error_file_list/<deployment_journal_id>', views.get_error_file_list, name='get_error_file_list'),
    path('upload-history', views.upload_history, name='upload-history'),
    # path('send_feedback', views.send_feedback, name='send_feedback'),
    path('feedback_request', views.feedback_request, name='feedback_request'),
    # path('send_upload_notification', views.send_upload_notification, name='send_upload_notification'), # wrapped by "upload_upload_history"
    path('update_upload_history/', views.update_upload_history, name='update_upload_history'),
    #path('check_upload_history/<int:deployment_journal_id>/', views.check_upload_history, name='check_upload_history'),
    path('update_is_read', views.update_is_read, name='update_is_read'),
    path('desktop', views.desktop, name='desktop'),
    path('announcement', views.announcement, name='announcement'),
    path('announcement_request', views.announcement_request, name='announcement_request'),
    path('announcement_is_read', views.announcement_is_read, name='announcement_is_read'),
    path('desktop_login', views.desktop_login, name='desktop-login'),
    path('desktop_login_verify/', views.desktop_login_verify, name='desktop-login-verify'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('api/dashboard/<chart>/', views.api_dashboard, name='api-dashboard'),
    path('404', views.page_404, name='page_404'),
    path('download_desktop_file', views.download_desktop_file, name='download_desktop_file'),
]
