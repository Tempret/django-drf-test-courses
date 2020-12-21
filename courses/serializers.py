from rest_framework import serializers

from .models import Course, CourseParticipant


class ReportSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    num_assigned = serializers.IntegerField()
    num_completed = serializers.IntegerField()


class CourseParticipantSerializer(serializers.ModelSerializer):
    first_name = serializers.StringRelatedField(source='student.first_name')
    last_name = serializers.StringRelatedField(source='student.first_name')
    email = serializers.StringRelatedField(source='student.email')

    class Meta:
        model = CourseParticipant
        fields = ['first_name', 'last_name', 'email']


class CourseSerializer(serializers.ModelSerializer):
    students_count = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    def get_students_count(self, obj: Course) -> int:
        return obj.participants.count()

    def get_participants(self, obj: Course) -> list:
        queryset = CourseParticipant.objects.filter(course=obj).select_related('student')[:10]

        return CourseParticipantSerializer(queryset, many=True).data

    class Meta:
        model = Course
        fields = ['name', 'start_date', 'end_date', 'students_count', 'participants']
