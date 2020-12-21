from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework_csv.renderers import CSVRenderer

from django.db.models import Count, Q

from courses.models import Course
from courses.serializers import CourseSerializer, ReportSerializer
from courses.exceptions import AlreadyAssignedException, NotAssignedException
from students.models import Student


class CoursesViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    renderer_classes = (CSVRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    @action(detail=True, methods=['post'], name='assign', url_path=r'assign/(?P<student_pk>[^/.]+)')
    def assign(self, request, student_pk=None, **kwargs) -> Response:
        course = self.get_object()

        try:
            course.assign_student(student_pk)
        except Student.DoesNotExist:
            raise NotFound('Student not found')
        except AlreadyAssignedException:
            raise ValidationError('Already assigned to course')

        return Response({}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], name='unassign', url_path=r'unassign/(?P<student_pk>[^/.]+)')
    def unassign(self, request, student_pk=None, **kwargs) -> Response:
        course = self.get_object()

        try:
            course.unassign_student(student_pk)
        except Student.DoesNotExist:
            raise NotFound('Student not found')
        except NotAssignedException:
            raise ValidationError('Student not assigned to course')

        return Response({}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], name='report')
    def report(self, request, **kwargs):
        query = Student.objects.all().annotate(
            num_assigned=Count('courses'),
            num_completed=Count('courses', filter=Q(courses__completed=True))
        )

        serializer = ReportSerializer(query, many=True)

        return Response(serializer.data)
