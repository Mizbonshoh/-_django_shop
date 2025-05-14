from .models import Product, OrderProduct, Order, Customer

class CartForAuthenticatesUser:
    """Логика корзины"""
    def __init__(self, request, product_id=None, action=None):
        self.user = request.user
        if product_id and action:
            self.add_or_delete(product_id, action)

    def get_cart_info(self):
        """Получение информации о корзине (кол-во и самма товара) и заказчике"""
        customer, created = Customer.objects.get_or_create(user=self.user)
        order, created = Order.objects.get_or_create(customer=customer)
        order_products = order.ordered.all()
        cart_total_quantity = order.get_cart_total_quantity
        cart_total_price = order.get_cart_total_price

        return {'order': order, # ID корзинки
                'order_products': order_products, # QuerySet объект товаров в корзине
                'cart_total_quantity': cart_total_quantity, # Общее кол-во товаров в корзине
                'cart_total_price': cart_total_price, # Общее стоимость товаров в корзине
                }

    def add_or_delete(self, product_id, action):
        """Добавление и удаление товара по нажатию плюс и минус"""
        order = self.get_cart_info()['order']
        product = Product.objects.get(pk=product_id)
        order_product, created = OrderProduct.objects.get_or_create(order=order, product=product)

        if action == 'add' and product.quantity > 0:
            order_product.quantity += 1
            product.quantity -= 1
        elif action == 'delete':
            order_product.quantity -= 1
            product.quantity += 1
        elif action == 'remove':
            product.quantity += order_product.quantity
            order_product.quantity -= order_product.quantity

        product.save()
        order_product.save()

        if order_product.quantity < 1:
            order_product.delete()

    def clear(self):
        """Удаление всех товаров с корзины"""
        order = self.get_cart_info()['order']
        orders_products = order.ordered.all()
        for product in orders_products:
            product.delete()
        order.save()

def get_cart_data(request):
    """Вывод товара с корзины на страницу"""
    cart = CartForAuthenticatesUser(request)
    cart_info = cart.get_cart_info()

    return {'order': cart_info['order'],
            'order_products': cart_info['order_products'],
            'cart_total_quantity': cart_info['cart_total_quantity'],
            'cart_total_price': cart_info['cart_total_price']}