from django.test import TestCase

from .models import Task


class TaskModelTest(TestCase):
    def setUp(self):
        Task.objects.create(title="Test Task 1")
        Task.objects.create(title="Test Task 2", completed=True)

    def test_task_creation(self):
        task1 = Task.objects.get(title="Test Task 1")
        task2 = Task.objects.get(title="Test Task 2")
        self.assertFalse(task1.completed)
        self.assertTrue(task2.completed)
