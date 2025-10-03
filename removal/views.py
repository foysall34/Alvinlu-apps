
import json
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from .models import Client, Task, TaskImage , TaskBoiler
from .serializers import ClientTaskSerializer, TaskCreateSerializer ,   TaskSerializer , TaskBoilerSerializer
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated

from django.db.models import Prefetch


class FilterClientTasksByDateView(APIView):
    def post(self, request, *args, **kwargs):
        date_str = request.data.get('date', None)

        if not date_str:
            return Response(
                {'error': 'A "date" field is required in the request body.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Please use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tasks_on_date = Task.objects.filter(created_at__date=target_date)
        if not tasks_on_date.exists():
            return Response([], status=status.HTTP_200_OK)

        clients_with_filtered_tasks = Client.objects.filter(
            tasks__in=tasks_on_date
        ).distinct().prefetch_related(
            Prefetch('tasks', queryset=tasks_on_date)
        )
        serializer = ClientTaskSerializer(clients_with_filtered_tasks, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskDateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user


        if hasattr(user, 'is_subscribed') and not user.is_subscribed:
    
            
            seven_days_ago = timezone.now().date() - timedelta(days=7)
            
         
            task_dates = Task.objects.filter(
                created_at__date__gte=seven_days_ago
            ).values('created_at')

     
            if not task_dates.exists():
                return Response({
                    "message": "No tasks found in the last 7 days. For older data, please buy a premium plan.",
                    "dates": []
                }, status=200)
        else:
         
            task_dates = Task.objects.values('created_at')

        return Response(list(task_dates))



class TaskAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        client_uid_str = request.query_params.get('client_uid')
        if not client_uid_str:
            return Response({'error': 'Query client_uid required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client = Client.objects.get(uid=uuid.UUID(client_uid_str))
            serializer = ClientTaskSerializer(client)
            return Response(serializer.data)
        except (ValueError, Client.DoesNotExist):
            return Response({'error': 'wring client_id'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        client_uid_str = request.data.get('client_uid')
        client = None
        if client_uid_str:
            try:
                client = Client.objects.get(uid=uuid.UUID(client_uid_str))
            except (ValueError, Client.DoesNotExist):
                return Response({'error': 'wrong client id'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            client = Client.objects.create()

        if client.tasks.count() >= 4:
            return Response(
                {'error': 'One client contain at least 4 steps'},
                status=status.HTTP_400_BAD_REQUEST
            )
        task_data = None

        if 'application/json' in request.content_type:
            task_data = request.data.get('task')
        else:
            task_data_str = request.data.get('task')
            if task_data_str:
                try:
                    task_data = json.loads(task_data_str)
                except json.JSONDecodeError:
                    return Response({'error': '"task is wrong json format'}, status=status.HTTP_400_BAD_REQUEST)

        if not task_data:
            return Response({'error': 'given task field in details'}, status=status.HTTP_400_BAD_REQUEST)

        task_serializer = TaskCreateSerializer(data=task_data)
        if task_serializer.is_valid():
            new_task = task_serializer.save(client=client)

            if 'multipart/form-data' in request.content_type:
                image_file = request.FILES.get('image')
                if image_file:
                    TaskImage.objects.create(task=new_task, image=image_file)
        else:
            return Response(task_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        client_serializer = ClientTaskSerializer(client)
        return Response(client_serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        client_uid_str = request.data.get('client_uid')
        if not client_uid_str:
            return Response({'error': 'client_uid is required'}, status=status.HTTP_400_BAD_REQUEST)

        task_id = request.data.get('task_id')
        if not task_id:
            return Response({'error': ' task_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(uid=uuid.UUID(client_uid_str))
            task = Task.objects.get(id=task_id, client=client)
        except (ValueError, Client.DoesNotExist):
            return Response({'error': 'there is no client id'}, status=status.HTTP_404_NOT_FOUND)
        except Task.DoesNotExist:
            return Response({'error': 'There is no task for this client id'}, status=status.HTTP_404_NOT_FOUND)

        task_data = None
        if 'application/json' in request.content_type:
            task_data = request.data.get('task')
        else:
            task_data_str = request.data.get('task')
            if task_data_str:
                try:
                    task_data = json.loads(task_data_str)
                except json.JSONDecodeError:
                    return Response({'error': '"task"  wrong json format'}, status=status.HTTP_400_BAD_REQUEST)

        if task_data:
            task_serializer = TaskCreateSerializer(task, data=task_data, partial=True)
            if task_serializer.is_valid():
                task_serializer.save()
            else:
                return Response(task_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'multipart/form-data' in request.content_type:
            image_file = request.FILES.get('image')

            if image_file:
                task_image, created = TaskImage.objects.get_or_create(task=task)
                task_image.image = image_file
                task_image.save()

        client_serializer = ClientTaskSerializer(client)
        return Response(client_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        client_uid_str = request.data.get('client_uid')
        if not client_uid_str:
            return Response({'error': 'client_uid is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(uid=uuid.UUID(client_uid_str))
        except (ValueError, Client.DoesNotExist):
            return Response({'error': 'wrong client id'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = client.tasks.all().delete()

        if count > 0:
            return Response({'message': f'Successfully deleted {count} tasks for the client.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No tasks found for the client to delete.'}, status=status.HTTP_200_OK)
    

class TaskBoilerViewSet(viewsets.ModelViewSet):
  
    queryset = TaskBoiler.objects.all()
    serializer_class = TaskBoilerSerializer

    def create(self, request, *args, **kwargs):


        if TaskBoiler.objects.count() >= 4:
        
            return Response(
                {'error': 'Maximum limit of 4 tasks has been reached. You cannot create more.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)



# For pdf generator views.py code 

import os
import uuid
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Client, TaskImage
from datetime import date, timedelta, datetime
from django.utils import timezone


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch


from PIL import Image

class GeneratePdfApiView(APIView):
    def post(self, request, *args, **kwargs):
        uids = request.data.get('uids') 
        date_filter = request.data.get('date_filter') 

        if not uids or not isinstance(uids, list):
            return Response({"error": "A list of UIDs is required."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Date Filtering Logic ---
        today = timezone.now().date()
        start_date = None

        if date_filter == 'today':
            start_date = today
        elif date_filter == 'recent': 
            start_date = today - timedelta(days=1)
        elif date_filter == 'this_week': 
            start_date = today - timedelta(days=6)

        clients = Client.objects.filter(uid__in=uids)
        if not clients:
            return Response({"error": "No clients found with the provided UIDs."}, status=status.HTTP_404_NOT_FOUND)

        # --- PDF Generation ---

        pdf_folder = os.path.join(settings.MEDIA_ROOT, 'pdfs')
        os.makedirs(pdf_folder, exist_ok=True)
        

        unique_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.pdf"
        pdf_path = os.path.join(pdf_folder, unique_filename)

        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        y_position = height - inch 


        def new_page():
            c.showPage()
            c.setFont("Helvetica-Bold", 12)
            y = height - inch
            c.drawString(inch, y, "Tasks List (Continued):")
            return y - 0.3 * inch

 
        for i, client in enumerate(clients):
 
            if i > 0:
                y_position = new_page()

  
            c.setFont("Helvetica-Bold", 16)
            c.drawString(inch, y_position, f"Task Report for Client: {client.uid}")
            y_position -= 0.3 * inch

            c.setFont("Helvetica", 12)
            c.drawString(inch, y_position, f"Report Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            y_position -= 0.5 * inch
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(inch, y_position, "Tasks List:")
            y_position -= 0.3 * inch

            tasks = client.tasks.all()

 
            if start_date:
                tasks = tasks.filter(created_at__date__gte=start_date, created_at__date__lte=today)

            for task in tasks:

                if y_position < 2 * inch:
                    y_position = new_page()

                # --- Task Details ---
                c.setFont("Helvetica-Bold", 11)
                c.drawString(inch, y_position, f"Task Name: {task.task_name}")
                y_position -= 0.25 * inch

                c.setFont("Helvetica", 10)
                c.drawString(1.2 * inch, y_position, f"- Target Time: {task.target_time}")
                y_position -= 0.2 * inch
                c.drawString(1.2 * inch, y_position, f"- Completion: {task.completion_percentage}%")
                y_position -= 0.2 * inch
                c.drawString(1.2 * inch, y_position, f"- Note: {task.note}")
                y_position -= 0.3 * inch

                # --- Add Images for the task ---
                images = task.images.all()
                if images:
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(1.2 * inch, y_position, "- Attached Images:")
                    y_position -= 0.25 * inch
                    
                    for task_image in images:
                        try:
                            image_path = task_image.image.path
                            
                            img = Image.open(image_path)
                            original_width, original_height = img.size
                            aspect = original_height / float(original_width)
                            
                            max_width = 3 * inch
                            display_height = max_width * aspect

                            if y_position - display_height < inch:
                                y_position = new_page()

                            c.drawImage(image_path, 1.4 * inch, y_position - display_height, width=max_width, height=display_height)
                            y_position -= (display_height + 0.2 * inch)

                        except FileNotFoundError:
                            if y_position < 1.5 * inch:
                               y_position = new_page()
                            c.setFont("Helvetica-Oblique", 9)
                            c.drawString(1.4 * inch, y_position, "[Image not found on server]")
                            y_position -= 0.2 * inch
                        except Exception as e:
                             if y_position < 1.5 * inch:
                               y_position = new_page()
                             c.setFont("Helvetica-Oblique", 9)
                             c.drawString(1.4 * inch, y_position, f"[Could not display image: {e}]")
                             y_position -= 0.2 * inch

                y_position -= 0.2 * inch 

        c.save()

    
        pdf_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, 'pdfs', unique_filename))
        return Response({'pdf_link': pdf_url}, status=status.HTTP_200_OK)
    



# For multiple uid, today , recent , this weeek task pdf 
import os
import uuid
from datetime import timedelta
from django.conf import settings
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML


class GenerateTaskReportView(APIView):
  
    def post(self, request, *args, **kwargs):
        uids = request.data.get('uids')
        filter_type = request.data.get('filter_type')

        if not uids and not filter_type:
            return Response(
                {'error': 'You must provide at least one filter: "uids" (a list) or "filter_type".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if uids and not isinstance(uids, list):
            return Response({'error': '"uids" must be a list of strings.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_filters = ['today', 'recent_task', 'this_week']
        if filter_type and filter_type not in allowed_filters:
            return Response({'error': f'Invalid "filter_type". Choose from: {allowed_filters}'}, status=status.HTTP_400_BAD_REQUEST)

      
        

        task_queryset = Task.objects.all()
        client_queryset = Client.objects.all()

  
        if filter_type:
            today = timezone.now().date()
            if filter_type == 'today':
                start_date = today
            elif filter_type == 'recent_task':  # Today + Yesterday
                start_date = today - timedelta(days=1)
            elif filter_type == 'this_week':  # Last 7 days including today
                start_date = today - timedelta(days=6)
            
            task_queryset = task_queryset.filter(created_at__date__gte=start_date, created_at__date__lte=today)
            

            client_queryset = client_queryset.filter(tasks__in=task_queryset).distinct()


        if uids:
            client_queryset = client_queryset.filter(uid__in=uids)

     
        final_clients = client_queryset.prefetch_related(
            Prefetch('tasks', queryset=task_queryset, to_attr='filtered_tasks')
        )

        context = {
            'clients': final_clients,
            'generation_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')
        }
        html_string = render_to_string('reports/task_report.html', context)
        
        report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        filename = f'task_report_{uuid.uuid4().hex}.pdf'
        pdf_path = os.path.join(report_dir, filename)

        HTML(string=html_string).write_pdf(pdf_path)

        pdf_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, 'reports', filename))

        return Response({'pdf_link': pdf_url}, status=status.HTTP_200_OK)
    



 
class ClientLatestTasksView(APIView):
   
    def post(self, request, *args, **kwargs):
        uid_str = request.data.get('uid')


        if not uid_str:
            return Response(
                {'error': 'A "uid" field is required in the request body.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            latest_four_tasks_prefetch = Prefetch(
                'tasks',
                queryset=Task.objects.order_by('-created_at')[:4]
            )

           
            client = Client.objects.prefetch_related(latest_four_tasks_prefetch).get(uid=uuid.UUID(uid_str))

        except Client.DoesNotExist:
        
            return Response(
                {'error': 'Client with the provided uid does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValueError, TypeError):
       
            return Response(
                {'error': 'Invalid UID format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ClientTaskSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)
    



# your_app_name/views.py

from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Min, Max, Count, F, Q, DurationField
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


from .models import Task, Client

def format_duration(duration):
    if duration is None:
        return "00:00"
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f'{hours:02}:{minutes:02}:{seconds:02}'
    return f'{minutes:02}:{seconds:02}'



class DashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        if hasattr(user, 'is_subscribed') and not user.is_subscribed:
            return Response(
                {'error': 'Your are free user. please buy premiun plan '}, 
                status=status.HTTP_403_FORBIDDEN
            )

        filter_type = request.data.get('filter_type')

        today = timezone.now()
        if filter_type == '1W':
            start_date = today - timedelta(weeks=1)
        elif filter_type == '1M':
            start_date = today - timedelta(days=30)
        elif filter_type == '6M':
            start_date = today - timedelta(days=180)
        elif filter_type == '1Y':
            start_date = today - timedelta(days=365)
        else:
            return Response({'error': 'Invalid filter_type. Use "1W", "1M", "6M", or "1Y".'}, status=status.HTTP_400_BAD_REQUEST)

        tasks = Task.objects.filter(created_at__gte=start_date)

        if not tasks.exists():
            return Response({'message': 'No task data found for the selected period.'}, status=status.HTTP_200_OK)

        avg_time_duration = tasks.aggregate(avg=Avg('current_time'))['avg']
        
        total_clients = tasks.values('client').distinct().count()
        total_tasks_count = tasks.count()
        on_time_tasks_count = tasks.filter(current_time__lte=F('target_time')).count()
        on_time_rate = (on_time_tasks_count / total_tasks_count * 100) if total_tasks_count > 0 else 0

        fastest_slowest = tasks.aggregate(fastest=Min('current_time'), slowest=Max('current_time'))

     
        step_names = TaskBoiler.objects.values_list('task_name', flat=True).distinct()
        
        step_analysis_data = []
        for name in step_names:
            step_tasks = tasks.filter(task_name=name)
            if step_tasks.exists():
                analysis = step_tasks.aggregate(
                    avg_current=Avg('current_time'),
                    avg_target=Avg('target_time'),
                    avg_completion=Avg('completion_percentage')
                )
             
                completion_percentage = min(round(analysis['avg_completion'] or 0), 100)
                
                step_analysis_data.append({
                    "name": name,
                    "current_time": format_duration(analysis['avg_current']),
                    "target_time": format_duration(analysis['avg_target']),
                    "completion_percentage": completion_percentage
                })
            else:
                step_analysis_data.append({
                    "name": name,
                    "current_time": "00:00",
                    "target_time": "00:00",
                    "completion_percentage": 0
                })

        if filter_type in ['1W', '1M']:
            trunc_kind = TruncDay('created_at')
            date_format = '%b %d'
        else:
            trunc_kind = TruncMonth('created_at')
            date_format = '%b %Y'

        trend_data = (
            tasks
            .annotate(period=trunc_kind)
            .values('period')
            .annotate(avg_duration=Avg('current_time'))
            .order_by('period')
        )
        
        labels = []
        dataset_data = []
        for item in trend_data:
            labels.append(item['period'].strftime(date_format))
            avg_seconds = item['avg_duration'].total_seconds() if item['avg_duration'] else 0
            dataset_data.append(round(avg_seconds))

        response_data = {
            "average_time": format_duration(avg_time_duration),
            "overview": {
                "date_range": f"{start_date.strftime('%b %d, %Y')} to {today.strftime('%b %d, %Y')}",
                "total_clients": total_clients,
                "on_time_rate": round(on_time_rate),
                "overtime_rate": round(100 - on_time_rate)
            },
            "performance": {
                "fastest": format_duration(fastest_slowest['fastest']),
                "slowest": format_duration(fastest_slowest['slowest'])
            },
            "step_analysis": step_analysis_data,
            "completion_time_trend": {
                "summary": f"{tasks.values('created_at__date').distinct().count()} service days . {total_tasks_count} services",
                "chart_data": {
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "Average Completion Time (seconds)",
                            "data": dataset_data,
                        }
                    ]
                }
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)