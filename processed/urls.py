from django.urls import path
from .views import new_task, mark_upload_complete, process_file, file_status, download_processed_file, user_files, delete_file

urlpatterns = [
    path('new-task/', new_task, name='new-task'),
    path('user-files/', user_files, name='user-files'),
    path('process-file/', process_file, name='process-file'),
    path('file-status/<str:task_id>/', file_status, name='file-status'),
    path('delete-file/<str:task_id>/', delete_file, name='delete-file'),
    path('mark-upload-complete/<str:task_id>/', mark_upload_complete, name='mark-upload-complete'),
    path('download-processed-file/<str:task_id>/', download_processed_file, name='download-processed-file'),
]
