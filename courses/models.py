from django.db import models

from students.models import Student
from .exceptions import AlreadyAssignedException, NotAssignedException


class CourseParticipant(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='participants')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='courses')
    completed = models.BooleanField(default=False, blank=False, null=False)

    class Meta:
        app_label = 'courses'
        db_table = 'course_participant'
        verbose_name = 'Course participant'
        verbose_name_plural = 'Course participants'
        unique_together = ('course', 'student')


class Course(models.Model):
    name = models.TextField()
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        app_label = 'courses'
        db_table = 'course'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def assign_student(self, student_id: int) -> None:
        student = Student.objects.get(id=student_id)

        if not CourseParticipant.objects.filter(course=self, student=student).exists():
            CourseParticipant.objects.create(course=self, student=student)
        else:
            raise AlreadyAssignedException

    def unassign_student(self, student_id: int) -> None:
        student = Student.objects.get(id=student_id)

        if CourseParticipant.objects.filter(course=self, student=student).exists():
            CourseParticipant.objects.get(course=self, student=student).delete()
        else:
            raise NotAssignedException
