from rest_framework import serializers
from .models import ProcessedFile

class ProcessedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedFile
        fields = ['task_id', 'status', 'unprocessed_file_url', 'processed_file_url']
