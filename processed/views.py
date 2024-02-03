import uuid
import boto3
import pandas as pd
import numpy as np
from joblib import load
from datetime import datetime
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ProcessedFile
from .serializers import ProcessedFileSerializer
import os
from dotenv import load_dotenv

load_dotenv()

# Create your views here.

def generate_task_id():
    return str(uuid.uuid4())

@api_view(['GET'])
def new_task(request):
    """
    @desc     Create a new task and return presigned URL for direct upload to S3
    @route    GET /api/v1/air-quality/new-task
    @access   Private
    @return   Json
    """
    try:
        task_id = generate_task_id()

        s3 = boto3.client('s3', region_name=os.environ.get('AWS_S3_REGION_NAME'))
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': os.environ.get('AWS_STORAGE_BUCKET_NAME'),
                'Key': f"{task_id}_unprocessed.csv",
                'ContentType': 'text/csv'
            },
            ExpiresIn=30000,
        )

        file_entry = ProcessedFile.objects.create(
            unprocessed_file_url=presigned_url,
            task_id=task_id,
            status='Ready to Upload'
        )

        serializer = ProcessedFileSerializer(file_entry)
        return Response({'message': 'Presigned URL generated successfully', 'data': serializer.data}, status=201)

    except Exception as e:
        return Response({'message': 'Failed to generate presigned URL', 'error': str(e)}, status=500)

@api_view(['POST'])
def mark_upload_complete(request):
    """
    @desc     Mark unprocessed file as ready to process after direct upload to S3
    @route    POST /api/v1/air-quality/mark-upload-complete/
    @access   Private
    @return   Json
    """
    task_id = request.data.get('task_id')
    try:

        file_entry = ProcessedFile.objects.get(task_id=task_id)
        file_entry.status = 'Ready to Process'
        file_entry.save()

        serializer = ProcessedFileSerializer(file_entry)
        return Response({'message': 'File marked as ready to process', 'data': serializer.data}, status=200)

    except ProcessedFile.DoesNotExist:
        return Response({'message': 'File not found'}, status=404)

    except Exception as e:
        return Response({'message': 'Failed to mark file as ready to process', 'error': str(e)}, status=500)

# Helper functions for preprocessing
def time_stamp_to_unix(datetime_str):
    datetime_object = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S UTC")
    return int(datetime_object.timestamp())

def preprocess_data(df):
    df['unix_timestamp'] = df['timestamp'].apply(time_stamp_to_unix)
    df.replace({'N/A': np.nan, 'Null': np.nan, 0: np.nan}, inplace=True)
    df.sort_values(by=['device_id', 'unix_timestamp'], inplace=True)

    return df.drop(columns=['timestamp'])

@api_view(['POST'])
def process_file(request):

    """
    @desc     Process unprocessed file and upload processed file to S3
    @route    POST /api/v1/air-quality/process-file
    @access   Private
    @return   Json
    """
        
    task_id = request.data.get('task_id')
    try:
        file_entry = ProcessedFile.objects.get(task_id=task_id)
        unprocessed_file_url = f"{os.environ.get('AWS_S3_BUCKET_URL')}/{task_id}_unprocessed.csv"

        df = pd.read_csv(unprocessed_file_url)
        df = preprocess_data(df)

        model = load('air_quality_rf_model.joblib')

        missing_indices = df[df.isnull().any(axis=1)].index

        if not missing_indices.empty:
            x_missing = df.loc[missing_indices, ['unix_timestamp', 'latitude', 'longitude']]
            df.loc[missing_indices, ['humidity', 'temperature', 'pm10', 'pm2_5']] = model.predict(x_missing)

        processed_file_path = f'{task_id}_processed.csv'
        df.to_csv(processed_file_path, index=False)

        s3 = boto3.client('s3', region_name=os.environ.get('AWS_S3_REGION_NAME'))
        response = s3.upload_file(processed_file_path, os.environ.get('AWS_STORAGE_BUCKET_NAME'), processed_file_path)
        processed_file_url = f"{os.environ.get('AWS_S3_BUCKET_URL')}/{processed_file_path}"

        file_entry.processed_file_url = processed_file_url
        file_entry.status = 'Processed'
        file_entry.save()

        return Response({
            'message': 'File processed successfully',
            'data': {
                'unprocessed_file_url': unprocessed_file_url,
                'processed_file_url': processed_file_url
            }
        }, status=200)

    except ProcessedFile.DoesNotExist:
        return Response({'message': 'File not found'}, status=404)
    except Exception as e:
        print(e)
        return Response({'message': f'Failed to process file: {str(e)}'}, status=500)

@api_view(['GET'])
def file_status(request):
    """
    @desc     Get the status of a processed file
    @route    GET /api/v1/air-quality/file-status/{task_id}
    @access   Private
    @return   Json
    """
    try:
        task_id = request.task_id
        file_entry = ProcessedFile.objects.get(task_id=task_id)

        serializer = ProcessedFileSerializer(file_entry)
        return Response({'status': file_entry.status, 'data': serializer.data}, status=200)

    except ProcessedFile.DoesNotExist:
        return Response({'message': 'File not found'}, status=404)

    except Exception as e:
        return Response({'message': 'Failed to retrieve file status', 'error': str(e)}, status=500)

@api_view(['GET'])
def download_processed_file(request):
    """
    @desc     Download the processed file
    @route    GET /api/v1/air-quality/download-processed-file/{task_id}
    @access   Private
    @return   HttpResponse
    """
    try:
        task_id = request.task_id

        file_entry = ProcessedFile.objects.get(ask_id=task_id)
        processed_file_url = file_entry.processed_file_url

        s3 = boto3.client('s3', region_name=os.environ.get('AWS_S3_REGION_NAME'))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{task_id}_processed.csv"'
        s3.download_fileobj('your-s3-bucket', processed_file_url, response)

        return response

    except ProcessedFile.DoesNotExist:
        return Response({'message': 'File not found'}, status=404)

    except Exception as e:
        return Response({'message': 'Failed to download processed file', 'error': str(e)}, status=500)
