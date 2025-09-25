from django.shortcuts import render
from django.views.generic import TemplateView
from products.models import Category, Product
from django.conf import settings
import os


class HomePageView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent__isnull=True)[:4]
        context['featured_products'] = Product.objects.filter(is_featured=True)[:4]
        return context


def about(request):
    return render(request, 'about.html', {})


def contact(request):
    if request.method == 'POST':
        # For now, just redirect back to the same page
        # Later we can add email sending functionality
        from django.contrib import messages
        messages.success(request, 'پیام شما با موفقیت ارسال شد.')
        from django.shortcuts import redirect
        return redirect('core:contact')
    return render(request, 'contact.html', {})


