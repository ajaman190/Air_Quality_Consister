from django.urls import path
from .views import new_task, mark_upload_complete, process_file, file_status, download_processed_file

urlpatterns = [
    path('new-task/', new_task, name='new-task'),
    path('process-file/', process_file, name='process-file'),
    path('file-status/<str:task_id>/', file_status, name='file-status'),
    path('mark-upload-complete/', mark_upload_complete, name='mark-upload-complete'),
    path('download-processed-file/<str:task_id>/', download_processed_file, name='download-processed-file'),
]
