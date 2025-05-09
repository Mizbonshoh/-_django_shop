from django.urls import path
from .views import *

urlpatterns = [
    path('', Index.as_view(), name='Index'),
    path('category/<slug:slug>/', SubCategories.as_view(), name='category_detail'),
    path('product/<slug:slug>/', ProductPage.as_view(), name='product_page'),
    path('login_registration/', login_registration, name='login_registration'),
    path('login', user_login, name='user_login'),
    path('logout', user_logout, name='user_logout'),
    path('register', user_registration, name='user_registration'),
    path('save_review/<int:product_pk>', save_review, name='save_review'),
    path('add_favorite/<slug:product_slug>/', save_favorite_product, name='add_favorite'),
]