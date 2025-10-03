from django.db import models
import uuid

class Client(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.uid)

class Task(models.Model):
    client = models.ForeignKey(Client, related_name='tasks', on_delete=models.CASCADE)
    task_name = models.CharField(max_length=200)
    current_time = models.DurationField()
    target_time = models.DurationField()
    completion_percentage = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.task_name

class TaskImage(models.Model):
    task = models.ForeignKey(Task, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='task_images/')

    def __str__(self):
        return f"Image for {self.task.task_name}"
    

class TaskBoiler(models.Model):
    client = models.ForeignKey(Client, related_name='taskds', on_delete=models.CASCADE , null= True )  
    task_name = models.CharField(max_length=200)
    current_time = models.DurationField()
    target_time = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)
    iconName = models.CharField(max_length=50, blank=True, null=True)
    iconColor = models.CharField(max_length=7, blank=True, null=True) 
    iconType = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.task_name