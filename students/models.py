from django.db import models


class Student(models.Model):
    """
    Model to store information about students
    """
    first_name = models.TextField()
    last_name = models.TextField()
    email = models.EmailField()

    def __str__(self) -> str:
        return f'{self.full_name} ({self.email})'

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'
