from django.conf.urls import url
from .import views

urlpatterns = [
    url("base/",views.base_layout,name='base'),
    url('check/',views.check,name='check'),
    url('login/',views.ulogin,name='login'),
    url('usage/',views.usage,name='usage'),
    url('payment/',views.payment,name='payment'),
    url('bill/',views.bill,name='bill'),
    url('email/',views.email,name='email')
]