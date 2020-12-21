import datetime

from rest_framework.test import APITransactionTestCase, APITestCase
from rest_framework.reverse import reverse
from django.utils import timezone
from courses.models import Course, CourseParticipant
from students.models import Student


class CoursesContext:
    """
        Simple context manager to create courses for tests and delete after
    """

    def __init__(self, number=1):
        Course.objects.bulk_create([
            Course(name=f'My avesome course #{_}',
                   description='no description',
                   start_date=timezone.now() - datetime.timedelta(days=2),
                   end_date=timezone.now() + datetime.timedelta(days=2))
            for _ in range(number)
        ])

        self.courses = Course.objects.all()

    def __enter__(self):
        return self.courses

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.courses.delete()


class StudentsContext:
    """
        Simple context manager to create students for tests and delete after
    """

    def __init__(self, number=1):
        Student.objects.bulk_create([
            Student(first_name=f'Student #{_}',
                    last_name='-',
                    email=f'student_{_}@mail.com')
            for _ in range(number)
        ])

        self.students = Student.objects.all()

    def __enter__(self):
        return self.students

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.students.delete()


class CoursesTestCase(APITransactionTestCase):

    def setUp(self):
        super(CoursesTestCase, self).setUp()
        headers = {
            'Accept': 'application/json',
            'Accept-Charset': 'utf-8',
            'Accept-Language': 'en-US',
            'Content-Type': 'application/json'
        }
        self.client.credentials(headers=headers)

    def test_courses_count(self) -> None:
        result = self.client.get(reverse('api:course-list'))

        self.assertEqual(len(result.data), 0, msg='Wrong entries count returned')

        with CoursesContext(10) as cources:
            result = self.client.get(reverse('api:course-list'))

            self.assertEqual(len(result.data), 10, msg='Wrong entries count returned')

    def test_courses_required_field_list(self) -> None:
        with CoursesContext(2) as courses:
            result = self.client.get(reverse('api:course-list'))

            self.assertEqual(
                sorted(list(result.data[0].keys())),
                sorted(['name', 'start_date', 'end_date', 'students_count', 'participants'])
            )

    def test_course_students_count(self) -> None:
        with CoursesContext() as courses, StudentsContext(2) as students:
            result = self.client.get(reverse('api:course-list'))

            # Check number of participants in first course
            self.assertEqual(result.data[0]['students_count'], 0, msg='Wrong students count')
            self.assertEqual(len(result.data[0]['participants']), 0, msg='Wrong participant list count')
            self.assertIsInstance(result.data[0]['participants'], list, msg='Wrong `participants` type')

            c = Course.objects.get(name=result.data[0]['name'])

            # Add two participants to first course
            CourseParticipant.objects.create(course=c, student=students[0])
            CourseParticipant.objects.create(course=c, student=students[1])

            result = self.client.get(reverse('api:course-list'))

            # Checking participants count after adding
            self.assertEqual(result.data[0]['students_count'], 2)
            self.assertEqual(len(result.data[0]['participants']), 2, msg='Wrong participant list count')
            self.assertEqual(
                sorted(list(result.data[0]['participants'][0].keys())),
                sorted(['first_name', 'last_name', 'email'])
            )
            self.assertIsInstance(result.data[0]['participants'], list, msg='Wrong `participants` type')

    def test_course_limit_participants(self) -> None:
        with CoursesContext(5) as courses, StudentsContext(20) as students:
            # To be sure that tested course haven't participants
            self.assertEqual(courses[0].participants.count(), 0)

            # Add participations
            CourseParticipant.objects.bulk_create([
                CourseParticipant(course=courses[0], student=student)
                for student in students
            ])

            with self.assertNumQueries(11):
                result = self.client.get(reverse('api:course-list'))

            self.assertEqual(courses[0].participants.count(), 20)
            self.assertEqual(result.data[0]['students_count'], 20)

            # To be sure that `participants` array have max 10 entries
            self.assertEqual(len(result.data[0]['participants']), 10)

            CourseParticipant.objects.all().delete()
            Student.objects.all().delete()

            self.assertEqual(courses[0].participants.count(), 0)

    def test_assign_to_course_validations(self) -> None:
        with CoursesContext() as courses, StudentsContext() as students:
            student = students[0]
            course = courses[0]

            # Return 404 if course does not exists
            result = self.client.post(reverse('api:course-assign', kwargs={'pk': 4242, 'student_pk': student.pk}))
            self.assertEqual(result.status_code, 404)

            # Return 404 if student does not exists
            result = self.client.post(reverse('api:course-assign', kwargs={'pk': course.pk, 'student_pk': 4242}))
            self.assertEqual(result.status_code, 404)

            result = self.client.post(reverse('api:course-assign', kwargs={'pk': course.pk, 'student_pk': student.pk}))
            self.assertEqual(result.status_code, 201)

            result = self.client.post(reverse('api:course-assign', kwargs={'pk': course.pk, 'student_pk': student.pk}))
            self.assertEqual(result.status_code, 400)
            self.assertEqual(result.data[0].code, 'invalid')
            self.assertEqual(str(result.data[0]), 'Already assigned to course')

            CourseParticipant.objects.all().delete()

    def test_assign_to_course(self) -> None:
        with CoursesContext() as courses, StudentsContext() as students:
            student = students[0]
            course = courses[0]

            # Check course before assignment
            list_result = self.client.get(reverse('api:course-list'))
            self.assertEqual(list_result.data[0]['students_count'], 0)

            result = self.client.post(reverse('api:course-assign', kwargs={'pk': course.pk, 'student_pk': student.id}))
            self.assertEqual(result.status_code, 201)

            # Check course after assignment
            list_result = self.client.get(reverse('api:course-list'))
            self.assertEqual(list_result.data[0]['students_count'], 1)
            self.assertEqual(len(list_result.data[0]['participants']), 1)
            self.assertEqual(list_result.data[0]['participants'][0]['first_name'], student.first_name)

    def test_unassign_from_course_validations(self) -> None:
        with CoursesContext() as courses, StudentsContext() as students:
            student = students[0]
            course = courses[0]

            # Return 404 if course does not exists
            result = self.client.post(reverse('api:course-unassign', kwargs={'pk': 4242, 'student_pk': student.pk}))
            self.assertEqual(result.status_code, 404)

            # Return 404 if student does not exists
            result = self.client.post(reverse('api:course-unassign', kwargs={'pk': course.pk, 'student_pk': 4242}))
            self.assertEqual(result.status_code, 404)

            # Trying unassing student who not assigned
            result = self.client.post(
                reverse('api:course-unassign', kwargs={'pk': course.pk, 'student_pk': student.pk}))
            self.assertEqual(result.status_code, 400)
            self.assertEqual(result.data[0].code, 'invalid')
            self.assertEqual(str(result.data[0]), 'Student not assigned to course')

    def test_unassign_from_course(self) -> None:
        with CoursesContext() as courses, StudentsContext() as students:
            student = students[0]
            course = courses[0]

            # Assing student to first course
            self.client.post(reverse('api:course-assign', kwargs={'pk': course.pk, 'student_pk': student.pk}))

            # Check course before unassignment
            list_result = self.client.get(reverse('api:course-list'))
            self.assertEqual(list_result.data[0]['students_count'], 1)

            self.client.post(reverse('api:course-unassign', kwargs={'pk': course.pk, 'student_pk': student.pk}))

            # Check course after unassignment
            with self.assertNumQueries(3):
                list_result = self.client.get(reverse('api:course-list'))
                self.assertEqual(list_result.data[0]['students_count'], 0)

    def test_report(self) -> None:
        with CoursesContext(10) as courses, StudentsContext(2) as students:

            with self.assertNumQueries(1):
                result = self.client.get(reverse('api:course-report'), {'format': 'json'})

            self.assertEqual(result.data[0]['num_assigned'], 0)
            self.assertEqual(result.data[0]['num_completed'], 0)

            self.assertEqual(result.data[1]['num_assigned'], 0)
            self.assertEqual(result.data[1]['num_completed'], 0)

            CourseParticipant.objects.create(student=students[0], course=courses[0])
            CourseParticipant.objects.create(student=students[0], course=courses[1])
            CourseParticipant.objects.create(student=students[0], course=courses[2], completed=True)
            CourseParticipant.objects.create(student=students[0], course=courses[3])
            CourseParticipant.objects.create(student=students[0], course=courses[4])

            with self.assertNumQueries(1):
                result = self.client.get(reverse('api:course-report'), {'format': 'csv'})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result['Content-Type'], 'text/csv; charset=utf-8')

            with self.assertNumQueries(1):
                result = self.client.get(reverse('api:course-report'), {'format': 'json'})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result['Content-Type'], 'application/json')

            self.assertEqual(result.data[0]['num_assigned'], 5)
            self.assertEqual(result.data[0]['num_completed'], 1)

            self.assertEqual(result.data[1]['num_assigned'], 0)
            self.assertEqual(result.data[1]['num_completed'], 0)

