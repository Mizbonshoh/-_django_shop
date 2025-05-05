from django.contrib import admin
from .models import Product, Category, Gallery
from django.utils.safestring import mark_safe


class GalleryInline(admin.TabularInline):
    fk_name = 'product'
    model = Gallery
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'get_product_count')
    prepopulated_fields = {'slug':('title', )}

    def get_product_count(self, obj):
        if obj.products:
            return str(len(obj.products.all()))
        else:
            return 0

    get_product_count.short_description = 'Кол-во товаров'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'category', 'quantity', 'price', 'created_at', 'size', 'color', 'get_photo')
    list_editable = ('price', 'quantity', 'size', 'color')
    prepopulated_fields = {'slug': ('title', )}
    list_filter = ('title', 'price')
    list_display_links = ('pk', 'title' )
    inlines = (GalleryInline, )

    def get_photo(self, obj):
        if obj.images.all():
            print(obj.images.all(),'---------0')
            print(obj.images.all()[0], '---------1')
            print(obj.images.all()[0].image, '---------2')
            print(obj.images.all()[0].image.url, '---------3')
            return mark_safe(f'<img src="{obj.images.all()[0].image.url}" width="75">')
        else:
            return 'none'
    get_photo.short_description = 'Миниатюра'


admin.site.register(Gallery)
