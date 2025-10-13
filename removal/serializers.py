
from rest_framework import serializers
from .models import Task, TaskImage, Client , TaskBoiler

class TaskImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskImage
        fields = ( 'id','image',)

class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id',
            'task_name',
            'current_time',
            'target_time',
            'completion_percentage',
            'note'
        )

class TaskSerializer(serializers.ModelSerializer):
    images = TaskImageSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Task
        fields = (
            'id',
            'task_name',
            'current_time',
            'target_time',
            'completion_percentage',
            'note',
            'created_at',
            'images'
        )

class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id',
            'task_name',
            'current_time',
            'target_time',
    
        )
           
class ClientTaskSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    uid_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = (  'uid_count' , 'uid', 'created_at', 'tasks')

    def get_uid_count(self, obj):
      
        return list(obj.tasks.values_list('id', flat=True))

class TaskImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskImage
        fields = ('image',)


class TaskBoilerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskBoiler

        fields = '__all__' 