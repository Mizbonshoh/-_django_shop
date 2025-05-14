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
    path('user_favorites/', FavoriteProductsView.as_view(), name='favorite_product_page'),
    path('save_email/', save_subscribers, name='save_subscribers'),
    path('send_mail/', send_mail_to_subscribers, name='send_mail'),
    path('cart/', cart, name='cart'),
    path('to_cart/<int:product_id>/<str:action>/', to_cart, name='to_cart'),
    path('checkout/', checkout, name='checkout'),
    path('payment/', create_checkout_session, name='payment'),
    path('payment_success/', successPayment, name='success'),
]