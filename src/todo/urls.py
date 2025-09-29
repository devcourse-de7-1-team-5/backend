from django.urls import path

from todo.views import TodoList, TotoDetail

urlpatterns = [
    path('todos/', TodoList.as_view(), name='todo_list'),
    path('todos/<int:pk>/', TotoDetail.as_view(), name='todo_detail')
]
