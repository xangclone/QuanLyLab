import os
import django
import sys
from django.conf import settings
from django.core.mail import send_mail

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

with open('mail_log.txt', 'w', encoding='utf-8') as f:
    try:
        f.write("Đang thử gửi mail kiểm tra...\n")
        send_mail(
            'Kiểm tra kết nối Email',
            'Nếu bạn nhận được email này, cấu hình SMTP của bạn đang hoạt động tốt.',
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER], 
            fail_silently=False,
        )
        f.write("Gửi mail THÀNH CÔNG!\n")
    except Exception as e:
        f.write(f"Gửi mail THẤT BẠI!\n")
        f.write(f"Lỗi chi tiết: {str(e)}\n")
