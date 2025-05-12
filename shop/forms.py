from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import *

class LoginFrom(AuthenticationForm):
    """Аутентификация пользователя"""
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'placeholder': 'Имя пользователя'}))

    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                             'placeholder': 'Пароль'}))


class RegistrationForm(UserCreationForm):
    """Регистрация пользователя"""
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                             'placeholder': 'Пароль'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                             'placeholder': 'Подтвердите пароль'}))

    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'}),
                  'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Почта'})}


class ReviewForm(forms.ModelForm):
    """Форма для отзыва"""
    class Meta:
        model = Review
        fields = ('text', 'grade')
        widgets = {'text' : forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ващ отзыв...'}),
                   'grade' : forms.Select(attrs={'class': 'form-control', 'placeholder': 'Ващ оценка'})}




class CustomerFrom(forms.ModelForm):
    """Контактная информация"""
    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'email', 'phone')
        widgets = {'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Вася'}),
                   'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
                   'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'examle@gmail.com'}),
                   'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7**********'})
                   }

class ShippingFrom(forms.ModelForm):
    """Адрес доставки"""
    class Meta:
        model = ShippingAddress
        fields = ('city', 'state', 'street')
        widgets = {'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Москва'}),
                   'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'МО'}),
                   'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Улица/Дом/Квартира...'})
                   }