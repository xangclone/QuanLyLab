from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Đổi admin mặc định của Django sang djangoadmin để dành chỗ cho trang quản lý Lab
    path('django-admin/', admin.site.urls),
    # Ưu tiên các trang của core
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
