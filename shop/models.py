from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

class Category(models.Model):
    title = models.CharField(max_length=150, verbose_name="Наименование категории")
    image = models.ImageField(upload_to='categories/', null=True, blank=True, verbose_name="Изображение")
    slug = models.SlugField(unique=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               verbose_name='Категория', related_name='subcategories')

    def get_absolute_url(self):
        """Ссылка на страницу категории"""
        return reverse('category_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'Категория: pk={self.pk}, title={self.title}'

    def get_parent_category_photo(self):
        """Для получения картинки родительского категории"""
        if self.image:
            return self.image.url
        else:
            return '-'


    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"



class Product(models.Model):
    title = models.CharField(max_length=255, verbose_name="Наименование товара")
    price = models.FloatField(verbose_name="Цена")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    watched = models.IntegerField(default=0, verbose_name="просмотры")
    quantity = models.IntegerField(default=0, verbose_name='Количество на складе')
    description = models.TextField(default='Здесь скоро будет описание', verbose_name='Описание товара')
    info = models.TextField(default='Дополнительная информация о продукта', verbose_name='Информация о товаре')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', related_name='products')
    slug = models.SlugField(unique=True, null=True)
    size = models.IntegerField(default=30, verbose_name='Размер в мм')
    color = models.CharField(max_length=30, default='Серебро', verbose_name='Цвет/Материал')


    def get_absolute_url(self):
        return reverse('product_page', kwargs={'slug': self.slug})

    def get_first_photo(self):
        if self.images.first():
            return self.images.first().image.url
        else:
            return 'Скоро здесь будет фото'

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'Товар: pk={self.pk}, title={self.title} price={self.price}'

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Товары'





class Gallery(models.Model):
    image = models.ImageField(upload_to='products/', verbose_name='Изображение')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')


    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Галерея товаров'


CHOICESS = (
    ('5', ('Отлично')),
    ('4', ('Хорошо')),
    ('3', ('Нормально')),
    ('2', ('Плохо')),
    ('1', ('Ужасно')),
)


class Review(models.Model):
    """Моделька для отзывов"""
    text = models.TextField(verbose_name='Текст')
    grade = models.CharField(max_length=20, choices=CHOICESS, blank=True, null=True, verbose_name='Оценка')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт')
    created_at = models.DateField(auto_now_add=True, verbose_name='Дата')

    def __str__(self):
        return self.author.username


    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class FavoriteProducts(models.Model):
    """Избранные товары"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')

    def __str__(self):
        return self.product.title

    class Meta:
        verbose_name = 'Избранный товар'
        verbose_name_plural = 'Избранные товары'


class Mail(models.Model):
    """Почтовая рассылка"""
    mail = models.EmailField(unique=True, verbose_name='Почта')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Пользователь')

    def __str__(self):
        return self.mail

    class Meta:
        verbose_name = 'Почта'
        verbose_name_plural = 'Почты'


class Customer(models.Model):
    """Контактная информация заказчика"""
    user = models.OneToOneField(User, models.SET_NULL, blank=True, null=True, verbose_name='Пользователь')
    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    email = models.EmailField(verbose_name='Почта')
    phone = models.CharField(max_length=255, verbose_name='Контактный номер')

    def __str__(self):
        return self.first_name

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Order(models.Model):
    """Корзина"""
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True,
                                 verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    is_completed = models.BooleanField(default=False, verbose_name='Зевершен')
    shipping = models.BooleanField(default=True, verbose_name='Доставка')

    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


    @property
    def get_cart_total_price(self):
        """Для получения суммы товаров в корзины"""
        order_products = self.ordered.all()
        total_price = sum([product.get_total_price for product in order_products])
        return total_price


    @property
    def get_cart_total_quantity(self):
        """Для получения общее количество товаров в корзине"""
        order_products = self.ordered.all()
        total_quantity = sum([product.quantity for product in order_products])
        return  total_quantity



class OrderProduct(models.Model):
    """Привязка продукта к корзине, строчки товаров"""
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name='ordered')
    quantity = models.IntegerField(default=0, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказах'


    @property
    def get_total_price(self):
        """Чтобы корзина смог подсчитать свою общую цену одного товара"""
        total_price = self.product.price * self.quantity
        return total_price


class ShippingAddress(models.Model):
    """Адрес доставки"""
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.street

    class Meta:
        verbose_name = 'Адрес доставка'
        verbose_name_plural = 'Адреса доставки'


