from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

class LabRoom(models.Model):
    """Định nghĩa thông tin phòng Lab"""
    name = models.CharField(max_length=100, verbose_name="Tên phòng Lab")
    capacity = models.IntegerField(verbose_name="Sức chứa")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả thiết bị")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Phòng Lab"
        verbose_name_plural = "Danh sách phòng Lab"

class Booking(models.Model):
    """Định nghĩa thông tin đặt phòng"""
    STATUS_CHOICES = [
        ('PENDING', 'Chờ duyệt'),
        ('APPROVED', 'Đã duyệt'),
        ('CANCELLED', 'Hủy'),
    ]

    lab_room = models.ForeignKey(LabRoom, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(verbose_name="Thời gian bắt đầu")
    end_time = models.DateTimeField(verbose_name="Thời gian kết thúc")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="Trạng thái")
    purpose = models.TextField(verbose_name="Mục đích sử dụng")

    class Meta:
        verbose_name = "Lịch đặt phòng"
        verbose_name_plural = "Danh sách lịch đặt"

    def clean(self):
        """
        Logic kiểm tra trùng lịch (Overlap Validation)
        Công thức: (StartA < EndB) AND (EndA > StartB)
        """
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError(_("Thời gian bắt đầu phải trước thời gian kết thúc."))

            # Chỉ kiểm tra trùng với các lịch đã được 'APPROVED'
            overlapping_bookings = Booking.objects.filter(
                lab_room=self.lab_room,
                status='APPROVED',
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )

            # Nếu là cập nhật (update), loại trừ chính bản thân nó khỏi danh sách kiểm tra
            if self.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)

            if overlapping_bookings.exists():
                raise ValidationError(
                    _("Phòng này đã có lịch được duyệt trong khoảng thời gian bạn chọn.")
                )

    def save(self, *args, **kwargs):
        self.full_clean() # Bắt buộc gọi clean() trước khi save
        super().save(*args, **kwargs)
