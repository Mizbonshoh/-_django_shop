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


from .models import Category, Product, Review, FavoriteProducts, Mail, Customer
from .forms import LoginFrom, RegistrationForm, ReviewForm, ShippingFrom, CustomerFrom
from .utils import CartForAuthenticatesUser, get_cart_data
from conf import settings



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

    def get_context_data(self,  **kwargs):
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
        context ['title'] = product.title
        # products = Product.objects.filter(category=product.category)
        #
        # data = []
        # for i in range(5):
        #     random_index = randint(0, len(products) - 1)
        #     random_product = products[random_index]
        #     if random_product not in data and str(random_product) != product.title:
        #         data.append(random_product)
        # context['products'] = data

        data = Product.objects.all().exclude(slug=self.kwargs['slug']).filter(category=product.category)[:5]
        context['products'] = data
        context['reviews'] = Review.objects.filter(product=product).order_by('-pk')
        if self.request.user.is_authenticated:
            context['review_form'] = ReviewForm
        return context

def login_registration(request):
    context = {'title': 'Войти или зарегистрировать',
               'login_form': LoginFrom,
               'registration_form': RegistrationForm, }

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
        # messages.error(request, 'Что-то пошло не так')
    return redirect('login_registration')


def save_review(request, product_pk):
    """Сохранение отзыва"""
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
        return redirect('login_registration')  # или другая страница для неавторизованных

    user = request.user
    product = get_object_or_404(Product, slug=product_slug)

    # Проверяем, есть ли уже товар в избранном
    fav_product_exists = FavoriteProducts.objects.filter(user=user, product=product).exists()

    if fav_product_exists:
        # Удаляем из избранного
        FavoriteProducts.objects.filter(user=user, product=product).delete()
    else:
        # Добавляем в избранное
        FavoriteProducts.objects.create(user=user, product=product)

    # Возвращаем на предыдущую страницу
    next_page = request.META.get('HTTP_REFERER', 'category_detail')
    return redirect(next_page)

class FavoriteProductsView(LoginRequiredMixin, ListView):
    """Для вывода избранных страниц"""
    model = FavoriteProducts
    context_object_name = 'products'
    template_name = 'shop/favorite_products.html'
    login_url = 'user_registration'


    def get_queryset(self):
        """Получаем товары конкретного пользователя"""
        user = self.request.user
        favs = FavoriteProducts.objects.filter(user=user)
        products = [ i.product for i in favs]
        return products


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
        mail_lists = Mail.objects.all()
        for email in mail_lists:
            print(email, '--------------------')
            send_mail(
                subject='У нас новая акция',
                message=text,
                from_email=settings.USER_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            print(f'Сообщение отправлено на почту: {email} -------- {bool(send_mail)}')
    context = {'title': 'Спамер'}
    return render(request, 'shop/send_mail.html', context)


def cart(request):
    """Страница корзины"""
    cart_info = get_cart_data(request)
    context = {'order': cart_info['order'],
               'order_products': cart_info['order_products'],
               'cart_total_quantity': cart_info['cart_total_quantity'],
               'title': 'Корзина'
               }

    return render(request, 'shop/cart.html', context)

def to_cart(request, product_id, action):
    """Добавить товар в корзину"""
    if request.user.is_authenticated:
        CartForAuthenticatesUser(request, product_id, action)
        return redirect('cart')
    else:
        messages.error(request, 'Авторизуйтесь или зарегистрируйтесь, чтобы совершать покупки')
        return redirect('login_registration')
    return redirect('cart')

def checkout(request):
    """Страница оформление заказа"""
    cart_info = get_cart_data(request)
    context = {'order': cart_info['order'],
               'order_products': cart_info['order_products'],
               'cart_total_quantity': cart_info['cart_total_quantity'],
               'customer_form': CustomerFrom(),
               'shipping_form': ShippingFrom(),
               'title': 'Оформление заказа'}
    return render(request, 'shop/checkout.html', context)


def create_checkout_session(request):
    """Оплата на STRIPE"""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if request.method == 'POST':
        user_cart = CartForAuthenticatesUser(request)
        cart_info = user_cart.get_cart_info()
        customer_form = CustomerFrom(data=request.POST)
        if customer_form.is_valid():
            customer = Customer.objects.get(user=request.user)
            customer.first_name = customer_form.cleaned_data['first_name']
            customer.last_name = customer_form.cleaned_data['last_name']
            customer.email = customer_form.cleaned_data['email']
            customer.phone = customer_form.cleaned_data['phone']
            customer.save()
        shipping_form = ShippingFrom(data=request.POST)
        if shipping_form.is_valid():
            address = shipping_form.save(commit=False)
            address.customer = Customer.objects.get(user=request.user)
            address.order = user_cart.get_cart_info()['order']
            address.save()

        total_price = cart_info['cart_total_price']
        total_quantity = cart_info['cart_total_quantity']

        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {'currency': 'usd',
                               'product_data': {'name': 'Товары сfd MsShop'},
                               'unit_amount': int(total_price * 100)},
                'quantity': total_quantity}],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('success'))

        )
        return redirect(session.url, 303)



def successPayment(request):
    """Оплата прошла успешна"""
    user_cart = CartForAuthenticatesUser(request)
    user_cart.clear()
    messages.success(request, 'Оплата прошла успешно')
    return render(request, 'shop/success.html')