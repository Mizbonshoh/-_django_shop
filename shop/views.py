from itertools import product
import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.utils import IntegrityError
from django.urls import reverse
from django.core import paginator
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
import logging

from .models import Category, Product, Review, FavoriteProducts, Mail, Customer
from .forms import LoginFrom, RegistrationForm, ReviewForm, ShippingFrom, CustomerFrom
from .utils import CartForAuthenticatedUser, get_cart_data
from conf import settings

logger = logging.getLogger(__name__)


class Index(ListView):
    """Главная страница"""
    model = Product
    context_object_name = 'categories'
    extra_context = {'title': 'Главная страница'}
    template_name = 'shop/index.html'

    def get_queryset(self):
        """Вывод родительской категории"""
        categories = Category.objects.filter(parent=None)
        return categories

    def get_context_data(self, **kwargs):
        """Вывод на страничку дополнительных элементов"""
        context = super().get_context_data()
        context['top_products'] = Product.objects.order_by('-watched')[:8]
        return context


class SubCategories(ListView):
    """Вывод подкатегории на отдельной страничке"""
    paginate_by = 3
    model = Product
    context_object_name = 'products'
    template_name = 'shop/category_page.html'

    def get_queryset(self):
        """Получение всех товаров подкатегории"""
        if type_field := self.request.GET.get('type'):
            products = Product.objects.filter(category__slug=type_field)
            return products

        parent_category = Category.objects.get(slug=self.kwargs['slug'])
        subcategories = parent_category.subcategories.all()
        products = Product.objects.filter(category__in=subcategories)

        if sort_field := self.request.GET.get('sort'):
            products = products.order_by(sort_field)

        return products

    def get_context_data(self, *, object_list=None, **kwargs):
        """Дополнительные элементы"""
        context = super().get_context_data()
        parent_category = Category.objects.get(slug=self.kwargs['slug'])
        context['category'] = parent_category
        context['title'] = parent_category.title
        return context


class ProductPage(DetailView):
    """Вывод товара на отдельной странице"""
    model = Product
    context_object_name = 'product'
    template_name = 'shop/product_page.html'

    def get_context_data(self, **kwargs):
        """Вывод на страничку дополнительных элементов"""
        context = super().get_context_data()
        product = Product.objects.get(slug=self.kwargs['slug'])
        context['title'] = product.title
        data = Product.objects.all().exclude(slug=self.kwargs['slug']).filter(category=product.category)[:5]
        context['products'] = data
        context['reviews'] = Review.objects.filter(product=product).order_by('-pk')
        if self.request.user.is_authenticated:
            context['review_form'] = ReviewForm
        return context


def login_registration(request):
    context = {'title': 'Войти или зарегистрировать',
               'login_form': LoginFrom,
               'registration_form': RegistrationForm}
    return render(request, 'shop/login_registration.html', context)


def user_login(request):
    """Аутентификация"""
    form = LoginFrom(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('Index')
    else:
        messages.error(request, 'Неверное имя пользователя или пароль')
        return redirect('login_registration')


def user_logout(request):
    """Выход пользователя"""
    logout(request)
    return redirect('Index')


def user_registration(request):
    """Регистрация пользователя"""
    form = RegistrationForm(data=request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Аккаунт пользователя успешно создан')
    else:
        for error in form.errors:
            messages.error(request, form.errors[error].as_text())
    return redirect('login_registration')


def save_review(request, product_pk):
    """Сохранение отзыва"""
    if not request.user.is_authenticated:
        return redirect('login_registration')

    form = ReviewForm(data=request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.author = request.user
        product = Product.objects.get(pk=product_pk)
        review.product = product
        review.save()
    return redirect('product_page', product.slug)


def save_favorite_product(request, product_slug):
    """Добавление или удаление товара из избранных"""
    if not request.user.is_authenticated:
        return redirect('login_registration')

    user = request.user
    product = get_object_or_404(Product, slug=product_slug)

    fav_product_exists = FavoriteProducts.objects.filter(user=user, product=product).exists()

    if fav_product_exists:
        FavoriteProducts.objects.filter(user=user, product=product).delete()
    else:
        FavoriteProducts.objects.create(user=user, product=product)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))


class FavoriteProductsView(LoginRequiredMixin, ListView):
    """Для вывода избранных страниц"""
    model = FavoriteProducts
    context_object_name = 'products'
    template_name = 'shop/favorite_products.html'
    login_url = 'login_registration'

    def get_queryset(self):
        """Получаем товары конкретного пользователя"""
        user = self.request.user
        favs = FavoriteProducts.objects.filter(user=user)
        return [item.product for item in favs]


def save_subscribers(request):
    """Собиратель почтовых адресов"""
    email = request.POST.get('email')
    user = request.user if request.user.is_authenticated else None
    if email:
        try:
            Mail.objects.create(mail=email, user=user)
        except IntegrityError:
            messages.error(request, 'Вы уже являетесь подписчиком')
    return redirect('Index')


def send_mail_to_subscribers(request):
    """Отправить писем подписчикам"""
    from django.core.mail import send_mail
    if request.method == 'POST':
        text = request.POST.get('text')
        for email in Mail.objects.values_list('mail', flat=True):
            send_mail(
                subject='У нас новая акция',
                message=text,
                from_email=settings.USER_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
    return render(request, 'shop/send_mail.html', {'title': 'Спамер'})


def cart(request):
    """Страница корзины"""
    if not request.user.is_authenticated:
        messages.error(request, 'Авторизуйтесь для просмотра корзины')
        return redirect('login_registration')

    try:
        cart_info = get_cart_data(request)
        context = {
            'order': cart_info['order'],
            'order_products': cart_info['order_products'],
            'cart_total_quantity': cart_info['cart_total_quantity'],
            'title': 'Корзина'
        }
        return render(request, 'shop/cart.html', context)
    except Exception as e:
        logger.error(f"Cart error: {str(e)}")
        messages.error(request, 'Ошибка при загрузке корзины')
        return redirect('index')


def to_cart(request, product_id, action):
    """Добавить товар в корзину"""
    if not request.user.is_authenticated:
        messages.error(request, 'Авторизуйтесь или зарегистрируйтесь, чтобы совершать покупки')
        return redirect('login_registration')

    try:
        CartForAuthenticatedUser(request, product_id, action)
        return redirect('cart')
    except Exception as e:
        logger.error(f"to_cart error: {str(e)}")
        messages.error(request, 'Ошибка при добавлении товара в корзину')
        return redirect('index')


def checkout(request):
    """Страница оформление заказа"""
    if not request.user.is_authenticated:
        return redirect('login_registration')

    cart_info = get_cart_data(request)
    context = {
        'order': cart_info['order'],
        'order_products': cart_info['order_products'],
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'customer_form': CustomerFrom(),
        'shipping_form': ShippingFrom(),
        'title': 'Оформление заказа'
    }
    return render(request, 'shop/checkout.html', context)


def create_checkout_session(request):
    """Оплата на STRIPE"""
    if not request.user.is_authenticated:
        return redirect('login_registration')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    if request.method == 'POST':
        try:
            user_cart = CartForAuthenticatedUser(request)
            cart_info = user_cart.get_cart_info()

            customer_form = CustomerFrom(data=request.POST)
            if customer_form.is_valid():
                customer, created = Customer.objects.get_or_create(user=request.user)
                customer.first_name = customer_form.cleaned_data['first_name']
                customer.last_name = customer_form.cleaned_data['last_name']
                customer.email = customer_form.cleaned_data['email']
                customer.phone = customer_form.cleaned_data['phone']
                customer.save()

            shipping_form = ShippingFrom(data=request.POST)
            if shipping_form.is_valid():
                address = shipping_form.save(commit=False)
                address.customer = Customer.objects.get(user=request.user)
                address.order = cart_info['order']
                address.save()

            session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'Товары с MsShop'},
                        'unit_amount': int(cart_info['cart_total_price'] * 100)
                    },
                    'quantity': cart_info['cart_total_quantity']
                }],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('success')),
                cancel_url=request.build_absolute_uri(reverse('cart'))
            )
            return redirect(session.url, 303)
        except Exception as e:
            logger.error(f"Checkout error: {str(e)}")
            messages.error(request, 'Ошибка при оформлении заказа')
            return redirect('checkout')
    return redirect('checkout')


def successPayment(request):
    """Оплата прошла успешно"""
    if request.user.is_authenticated:
        try:
            user_cart = CartForAuthenticatedUser(request)
            user_cart.clear()
            messages.success(request, 'Оплата прошла успешно')
        except Exception as e:
            logger.error(f"Success payment error: {str(e)}")
    return render(request, 'shop/success.html')