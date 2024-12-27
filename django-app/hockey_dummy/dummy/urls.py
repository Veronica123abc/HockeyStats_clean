from django.urls import path
from . import views

urlpatterns = [
    path('menu/', views.menu_view, name='menu'),
    path('dummy/', views.dummy_view, name='dummy'),
    path('dummy_image_view/<str:chart_type>/', views.dummy_image_view, name='dummy_image_view'),
]
