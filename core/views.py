from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import json
import os
import csv
from datetime import datetime, timedelta
from .booking_service import LabBookingService

# --- Cấu hình Email Template ---
LOGO_URL = "https://vlu.edu.vn/images/vlu-logo.png"

def get_email_template(title, content, footer_note=""):
    return f"""
    <div style="font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto; color: #333; line-height: 1.6; border: 1px solid #ddd; padding: 0;">
        <div style="text-align: center; padding: 20px; border-bottom: 1px solid #eee;">
            <img src="{LOGO_URL}" alt="VLU" style="height: 50px;">
            <div style="font-weight: bold; font-size: 18px; margin-top: 10px; color: #000;">{title}</div>
        </div>
        
        <div style="padding: 30px;">
            {content}
        </div>
        
        <div style="font-size: 12px; color: #777; background-color: #f9f9f9; padding: 20px; border-top: 1px solid #eee;">
            {footer_note}
            <div style="margin-top: 10px; font-weight: bold; color: #444;">KHOA KỸ THUẬT CƠ ĐIỆN VÀ MÁY TÍNH - ĐẠI HỌC VĂN LANG</div>
            <div>Địa chỉ: 69/68 Đặng Thùy Trâm, P.13, Q. Bình Thạnh, TP.HCM</div>
            <div>Liên hệ: (028) 7105 9999 | Email: p.qlcs@vlu.edu.vn</div>
        </div>
    </div>
    """

def get_info_table(data_map):
    rows = ""
    for label, value in data_map.items():
        rows += f"""
        <tr>
            <td style="padding: 10px; border: 1px solid #eee; background-color: #fcfcfc; font-weight: bold; width: 140px;">{label}</td>
            <td style="padding: 10px; border: 1px solid #eee;">{value}</td>
        </tr>
        """
    return f'<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">{rows}</table>'

# --- Views ---

def dashboard_view(request):
    return render(request, 'core/dashboard.html')

def calendar_view(request):
    return render(request, 'core/booking_form.html')

def student_register_view(request):
    return render(request, 'core/student_register.html')

def history_view(request):
    return render(request, 'core/history.html')

@staff_member_required
def admin_dashboard_view(request):
    return render(request, 'core/admin_dashboard.html')

@csrf_exempt
def api_create_booking(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service = LabBookingService()
            success, msg = service.validate_and_create(data)
            
            if success:
                # Gửi mail thông báo cho Admin kèm bảng thông tin
                info = {
                    "Người đăng ký": f"{data.get('user')} ({data.get('mssv')})",
                    "Email": data.get('email'),
                    "Phòng Lab": data.get('lab_name'),
                    "Thời gian": data.get('start_time').replace('T', ' '),
                    "Mục đích": data.get('purpose'),
                    "Hình thức": f"{data.get('type')} ({data.get('group_size')} người)"
                }
                content = f"<p>Hệ thống nhận được yêu cầu đăng ký mới:</p>{get_info_table(info)}"
                content += f'<p style="text-align:center;"><a href="{request.build_absolute_uri("/admin/")}" style="background-color:#333; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px;">ĐI ĐẾN TRANG QUẢN TRỊ</a></p>'
                
                html = get_email_template("THÔNG BÁO ĐĂNG KÝ MỚI", content)
                try:
                    send_mail(f"THÔNG BÁO ĐĂNG KÝ MỚI", "", settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], html_message=html)
                except: pass
                return JsonResponse({'status': 'success', 'message': 'Đã gửi đơn, vui lòng chờ phê duyệt.'})
            return JsonResponse({'status': 'error', 'message': msg})
        except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
@staff_member_required
def api_update_booking_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            bid, status, reason = data.get('id'), data.get('status'), data.get('reason', 'Không có lý do cụ thể.')
            service = LabBookingService()
            if service.update_booking_status(bid, status):
                b = next((i for i in service.get_bookings() if str(i.get('id', i.get('ID'))) == str(bid)), None)
                if b and (b.get('email') or b.get('Email')):
                    email = b.get('email') or b.get('Email')
                    
                    info = {
                        "Họ và tên": b.get('user', b.get('User')),
                        "MSSV": b.get('mssv', b.get('MSSV')),
                        "Phòng Lab": b.get('lab_name', b.get('LabName')),
                        "Thời gian": str(b.get('start_time', b.get('StartTime'))).replace('T', ' ')
                    }
                    
                    if status == 'APPROVED':
                        url = request.build_absolute_uri(reverse('confirm-booking') + f'?bid={bid}')
                        title = "ĐƠN ĐĂNG KÝ ĐÃ ĐƯỢC PHÊ DUYỆT"
                        content = f"<p>Chào {b.get('user', b.get('User'))}, đơn của bạn đã được phê duyệt với thông tin sau:</p>{get_info_table(info)}"
                        content += f'<p style="text-align:center; margin-top:25px;"><a href="{url}" style="background-color:#d32f2f; color:#fff; padding:12px 25px; text-decoration:none; border-radius:4px; font-weight:bold;">XÁC NHẬN & ĐỒNG BỘ LỊCH</a></p>'
                        note = "* Lưu ý: Bạn bắt buộc phải nhấn nút Xác nhận ở trên để hoàn tất thủ tục giữ chỗ."
                    else:
                        title = "ĐƠN ĐĂNG KÝ BỊ TỪ CHỐI"
                        info["Lý do từ chối"] = f'<span style="color:red;">{reason}</span>'
                        content = f"<p>Chào {b.get('user', b.get('User'))}, Ban quản lý rất tiếc phải từ chối đơn đăng ký của bạn:</p>{get_info_table(info)}"
                        note = "Mọi thắc mắc vui lòng liên hệ văn phòng khoa."
                    
                    html = get_email_template(title, content, note)
                    send_mail(f"[VLU LAB] Kết quả đăng ký: {b.get('lab_name')}", "", settings.EMAIL_HOST_USER, [email], html_message=html)
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error'})
        except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

def confirm_booking(request):
    bid = request.GET.get('bid')
    service = LabBookingService()
    if service.update_booking_status(bid, 'APPROVED'):
        b = next((i for i in service.get_bookings() if str(i.get('id', i.get('ID'))) == str(bid)), None)
        if b:
            cal_success, cal_link = service.add_to_calendar(b)
            if cal_success:
                email = b.get('email', b.get('Email'))
                info = {
                    "Phòng Lab": b.get('lab_name'),
                    "Thời gian": str(b.get('start_time')).replace('T', ' '),
                    "Trạng thái": "Đã đồng bộ Calendar"
                }
                content = f"<p>Chúc mừng bạn đã xác nhận thành công!</p>{get_info_table(info)}"
                content += f'<p><a href="{cal_link}">[Nhấn vào đây để xem trên Lịch Google]</a></p>'
                html = get_email_template("XÁC NHẬN THÀNH CÔNG", content, "Vui lòng có mặt đúng giờ.")
                send_mail("[VLU LAB] Hoàn tất xác nhận sử dụng Lab", "", settings.EMAIL_HOST_USER, [email], html_message=html)
                return render(request, 'core/confirm_success.html', {'status': 'success', 'message': 'Xác nhận thành công!', 'link': cal_link})
    return render(request, 'core/confirm_success.html', {'status': 'error', 'message': 'Lỗi hệ thống hoặc link đã hết hạn.'})

@csrf_exempt
@staff_member_required
def api_resend_booking_email(request):
    if request.method == 'POST':
        try:
            bid = json.loads(request.body).get('id')
            service = LabBookingService()
            b = next((i for i in service.get_bookings() if str(i.get('id', i.get('ID'))) == str(bid)), None)
            if b:
                url = request.build_absolute_uri(reverse('confirm-booking') + f'?bid={bid}')
                info = {
                    "Phòng Lab": b.get('lab_name'),
                    "Thời gian": str(b.get('start_time')).replace('T', ' '),
                    "MSSV": b.get('mssv')
                }
                content = f"<p>Ban quản lý gửi lại thông tin xác nhận phê duyệt cho <b>{b.get('user', b.get('User'))}</b>:</p>{get_info_table(info)}"
                content += f'<p style="text-align:center; margin-top:25px;"><a href="{url}" style="background-color:#d32f2f; color:#fff; padding:12px 25px; text-decoration:none; border-radius:4px; font-weight:bold;">XÁC NHẬN & ĐỒNG BỘ LỊCH</a></p>'
                html = get_email_template("GỬI LẠI THÔNG BÁO PHÊ DUYỆT", content, "* Vui lòng nhấn nút xác nhận để hoàn tất thủ tục.")
                send_mail(f"[VLU LAB] (Gửi lại) Thông báo phê duyệt - {b.get('lab_name')}", "", settings.EMAIL_HOST_USER, [b.get('email', b.get('Email'))], html_message=html)
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error'})
        except: return JsonResponse({'status': 'error'})

# --- Phụ trợ ---
def get_labs_list(request):
    try: return JsonResponse(LabBookingService().get_labs() or [], safe=False)
    except: return JsonResponse([], safe=False)

def get_lab_availability(request):
    try: return JsonResponse(LabBookingService().get_availability(request.GET.get('lab_id'), request.GET.get('date')), safe=False)
    except: return JsonResponse({'error': 'Lỗi'}, status=500)

@csrf_exempt
def api_register_student(request):
    if request.method == 'POST':
        success, msg = LabBookingService().add_student(json.loads(request.body))
        return JsonResponse({'status': 'success' if success else 'error', 'message': msg})

@staff_member_required
def api_get_auto_approval(request):
    return JsonResponse({'auto_approval': LabBookingService().get_auto_approval()})

@csrf_exempt
@staff_member_required
def api_update_auto_approval(request):
    if request.method == 'POST':
        success = LabBookingService().update_auto_approval(json.loads(request.body).get('status'))
        return JsonResponse({'status': 'success' if success else 'error'})

@staff_member_required
def api_get_students(request):
    try: return JsonResponse(LabBookingService().get_students(), safe=False)
    except: return JsonResponse([], safe=False)

def api_get_bookings_list(request):
    try: return JsonResponse(LabBookingService().get_bookings(), safe=False)
    except: return JsonResponse([], safe=False)

@csrf_exempt
@staff_member_required
def api_update_student_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Handle both 'id' and 'mssv' keys to be safe
        student_id = data.get('id') or data.get('mssv')
        success = LabBookingService().update_student_status(student_id, data.get('status'))
        return JsonResponse({'status': 'success' if success else 'error'})

def get_booking_events(request):
    try: return JsonResponse([{'id': r.get('id'), 'title': f"[{r.get('lab_name')}] {r.get('user')}", 'start': r.get('start_time'), 'end': r.get('end_time'), 'backgroundColor': '#28a745' if r.get('status') == 'APPROVED' else '#ffc107'} for r in LabBookingService().get_bookings()], safe=False)
    except: return JsonResponse([], safe=False)

def api_get_availability_events(request):
    try:
        service = LabBookingService()
        lab_id = request.GET.get('lab_id')
        start_date_str = request.GET.get('start', '').split('T')[0]
        end_date_str = request.GET.get('end', '').split('T')[0]
        
        if not lab_id: return JsonResponse([], safe=False)

        curr = datetime.strptime(start_date_str, '%Y-%m-%d')
        end = datetime.strptime(end_date_str, '%Y-%m-%d')
        events = []
        
        while curr <= end:
            d_str = curr.strftime('%Y-%m-%d')
            slots = service.get_availability(lab_id, d_str)
            for s in slots:
                available = s.get('available', 0)
                color = '#22c55e' # Green
                if available <= 0: color = '#ef4444' # Red
                elif available < 10: color = '#f59e0b' # Warning
                
                events.append({
                    'title': f"Trống: {available}",
                    'start': s['start_iso'],
                    'end': s['end_iso'],
                    'backgroundColor': color,
                    'borderColor': color,
                    'extendedProps': {
                        'available': available,
                        'total': s['total'],
                        'status_msg': s['status_msg']
                    }
                })
            curr += timedelta(days=1)
        return JsonResponse(events, safe=False)
    except: return JsonResponse([], safe=False)

@csrf_exempt
def api_hygiene_report(request):
    if request.method == 'POST':
        try:
            image_url = ''
            if 'image' in request.FILES:
                fs = FileSystemStorage(location=os.path.join('media', 'hygiene'))
                filename = fs.save(request.FILES['image'].name, request.FILES['image'])
                image_url = request.build_absolute_uri(f"/media/hygiene/{filename}")
            success, msg = LabBookingService().add_hygiene_report({**request.POST.dict(), 'image_url': image_url})
            return JsonResponse({'status': 'success' if success else 'error', 'message': msg})
        except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)})

def api_get_hygiene_reports(request):
    try: return JsonResponse(LabBookingService().get_hygiene_reports(), safe=False)
    except: return JsonResponse([], safe=False)

def api_export_bookings_csv(request):
    try:
        f_name = request.GET.get('name', '').lower()
        all_bookings = LabBookingService().get_bookings()
        filtered = [b for b in all_bookings if (not f_name or f_name in str(b.get('user', b.get('User', ''))).lower() or f_name in str(b.get('mssv', b.get('MSSV', ''))).lower())]
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="BaoCao_Lab.csv"'
        response.write('\ufeff'.encode('utf8'))
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['MSSV', 'Họ Tên', 'Phòng', 'Bắt Đầu', 'Kết Thúc', 'Trạng Thái'])
        for b in filtered:
            writer.writerow([b.get('mssv', b.get('MSSV')), b.get('user', b.get('User')), b.get('lab_name', b.get('LabName')), b.get('start_time', b.get('StartTime')), b.get('end_time', b.get('EndTime')), b.get('status', b.get('Status'))])
        return response
    except Exception as e: return JsonResponse({'error': str(e)}, status=500)
