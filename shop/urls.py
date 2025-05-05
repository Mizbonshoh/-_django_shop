from django.urls import path
from .views import *

urlpatterns = [
    path('', Index.as_view(), name='Index'),
    path('category/<slug:slug>/', SubCategories.as_view(), name='category_detail'),
]