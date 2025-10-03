from django.contrib import admin
from .models import Task, TaskImage , Client  , TaskBoiler



admin.site.register(TaskImage)
# admin.site.register(Client)

@admin.register(Client) 
class Myclient(admin.ModelAdmin):

    list_display = ['uid_count', 'uid', 'created_at']
    

    def uid_count(self, obj):
        return obj.tasks.count()

    
    uid_count.short_description = 'Total Tasks'
    
    


@admin.register(Task)
class CustomerTask(admin.ModelAdmin):
    list_display = (
        'id',
        'task_name',
        'client', 
        'target_time',
        'completion_percentage',
        'created_at',
    )




@admin.register(TaskBoiler)
class BoilerTask(admin.ModelAdmin):
    list_display = (
        'id',
        'task_name')



