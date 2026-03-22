import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
import os

class LabBookingService:
    SLOTS = [
        {"id": 1, "name": "Ca 1", "start": "07:00", "end": "09:30"},
        {"id": 2, "name": "Ca 2", "start": "09:30", "end": "12:00"},
        {"id": 3, "name": "Ca 3", "start": "13:00", "end": "15:30"},
        {"id": 4, "name": "Ca 4", "start": "15:30", "end": "18:00"},
    ]

    def __init__(self):
        self.sheet = None
        self.booking_sheet = None
        self.lab_sheet = None
        self.student_sheet = None
        self.hygiene_sheet = None
        self.notes_sheet = None
        self.config_sheet = None
        self.error_msg = None
        self.creds = None # Lưu credentials để dùng cho Calendar

        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets', 
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/calendar'
            ]
            cred_path = os.path.join(os.getcwd(), 'credentials.json')
            
            # Ưu tiên đọc từ biến môi trường (Cho Vercel/Deploy)
            env_creds = os.environ.get('GOOGLE_CREDENTIALS')
            if env_creds:
                import json
                info = json.loads(env_creds)
                self.creds = Credentials.from_service_account_info(info, scopes=scope)
            elif os.path.exists(cred_path):
                self.creds = Credentials.from_service_account_file(cred_path, scopes=scope)
            else:
                self.error_msg = "Không tìm thấy file credentials.json hoặc biến GOOGLE_CREDENTIALS"
                return
            self.client_email = self.creds.service_account_email
            client = gspread.authorize(self.creds)
            
            try:
                sheet_id = '11TBgqd-LQfN3m35TKuN1d_psCZQQ6sFBlJ7vFrT4wko'
                self.sheet = client.open_by_key(sheet_id)
                
                def get_ws(name, index):
                    try: return self.sheet.worksheet(name)
                    except:
                        try: return self.sheet.get_worksheet(index)
                        except: return None

                self.booking_sheet = get_ws('DatPhong', 0)
                self.lab_sheet = get_ws('DanhSachLab', 1)
                self.student_sheet = get_ws('SinhVien', 2)
                self.hygiene_sheet = get_ws('VeSinh', 3)
                self.notes_sheet = get_ws('GhiChu', 4)
                self.config_sheet = get_ws('CauHinh', 5)

            except Exception as e:
                self.error_msg = f"Lỗi mở Sheet: {str(e)}"

        except Exception as e:
            self.error_msg = f"Lỗi khởi tạo: {str(e)}"

    def add_to_calendar(self, booking_data):
        try:
            from googleapiclient.discovery import build
            service = build('calendar', 'v3', credentials=self.creds)
            
            # Lấy giá trị thời gian, hỗ trợ cả hai kiểu viết tiêu đề cột
            raw_start = booking_data.get('start_time') or booking_data.get('StartTime') or booking_data.get('start_iso')
            raw_end = booking_data.get('end_time') or booking_data.get('EndTime') or booking_data.get('end_iso')
            
            if not raw_start or not raw_end:
                return False, f"Không tìm thấy dữ liệu thời gian: Start={raw_start}, End={raw_end}"

            # Đảm bảo định dạng thời gian là ISO 8601 (RFC3339)
            start_time = str(raw_start).replace(' ', 'T')
            end_time = str(raw_end).replace(' ', 'T')
            
            # Thêm giây nếu thiếu (ví dụ: 2024-03-22T07:00 -> 2024-03-22T07:00:00)
            if 'T' in start_time and len(start_time.split('T')[1]) <= 5: start_time += ":00"
            if 'T' in end_time and len(end_time.split('T')[1]) <= 5: end_time += ":00"

            event = {
                'summary': f"Sử dụng Lab: {booking_data.get('lab_name', booking_data.get('LabName', 'VLU'))}",
                'location': f"Phòng Lab {booking_data.get('lab_name', booking_data.get('LabName', ''))}, VLU",
                'description': f"Người đăng ký: {booking_data.get('user', booking_data.get('User'))} ({booking_data.get('mssv', booking_data.get('MSSV'))})\nMục đích: {booking_data.get('purpose', booking_data.get('Purpose', ''))}",
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'Asia/Ho_Chi_Minh',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'Asia/Ho_Chi_Minh',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            event = service.events().insert(calendarId='primary', body=event).execute()
            return True, event.get('htmlLink')
        except Exception as e:
            return False, f"Lỗi Calendar: {str(e)}"

    def get_auto_approval(self):
        try:
            if not self.config_sheet: return False
            val = self.config_sheet.cell(1, 2).value 
            return str(val).upper() == 'TRUE'
        except: return False

    def update_auto_approval(self, status):
        try:
            if not self.config_sheet: return False
            self.config_sheet.update_cell(1, 2, 'TRUE' if status else 'FALSE')
            return True
        except: return False

    def get_labs(self):
        try:
            if not self.lab_sheet: return []
            data = self.lab_sheet.get_all_records()
            if not data: return []
            return [r for r in data if str(r.get('id', r.get('ID', ''))).strip()]
        except Exception as e:
            print(f"Error get_labs: {e}")
            return []

    def get_bookings(self):
        try:
            if not self.booking_sheet: return []
            data = self.booking_sheet.get_all_records()
            if not data: return []
            return [r for r in data if str(r.get('id', r.get('ID', ''))).strip()]
        except Exception as e:
            print(f"Error get_bookings: {e}")
            return []

    def get_students(self):
        try:
            if not self.student_sheet: return []
            data = self.student_sheet.get_all_records()
            if not data: return []
            return [r for r in data if str(r.get('mssv', r.get('MSSV', ''))).strip()]
        except Exception as e:
            print(f"Error get_students: {e}")
            return []

    def get_hygiene_reports(self):
        try:
            if not self.hygiene_sheet: return []
            data = self.hygiene_sheet.get_all_records()
            return [r for r in data if str(r.get('lab_id', r.get('LabID', ''))).strip()]
        except: return []

    def get_schedule_notes(self):
        try:
            if not self.notes_sheet: return []
            return self.notes_sheet.get_all_records()
        except: return []

    def get_availability(self, lab_id, date_str):
        try:
            labs = self.get_labs()
            lab_info = next((l for l in labs if str(l.get('id', l.get('ID'))) == str(lab_id)), None)
            total_capacity = 40
            if lab_info:
                try:
                    cap = lab_info.get('capacity', lab_info.get('Capacity', 40))
                    total_capacity = int(cap) if cap else 40
                except: pass

            notes = self.get_schedule_notes()
            special_event = next((n for n in notes if str(n.get('date')) == date_str and (str(n.get('lab_id')) == "ALL" or str(n.get('lab_id')) == str(lab_id))), None)
            
            if special_event:
                return [{"slot_id": s['id'], "name": s['name'], "time": f"{s['start']} - {s['end']}", "available": 0, "total": total_capacity, "status_msg": special_event.get('note', 'Đóng cửa'), "type": special_event.get('type', 'CLOSED')} for s in self.SLOTS]
            
            bookings = self.get_bookings()
            results = []
            for slot in self.SLOTS:
                total_used = 0
                slot_start_iso = f"{date_str}T{slot['start']}:00"
                slot_start_alt = slot_start_iso.replace('T', ' ')
                
                for b in bookings:
                    b_lab = str(b.get('lab_id', b.get('LabID', '')))
                    b_start = str(b.get('start_time', b.get('StartTime', '')))
                    b_status = str(b.get('status', b.get('Status', ''))).upper()
                    if b_lab == str(lab_id) and (b_start == slot_start_iso or b_start == slot_start_alt) and b_status == 'APPROVED':
                        try:
                            size = int(b.get('group_size', b.get('GroupSize', 1)))
                        except: size = 1
                        total_used += size
                
                results.append({
                    "slot_id": slot['id'], "name": slot['name'], "time": f"{slot['start']} - {slot['end']}", 
                    "available": max(0, total_capacity - total_used), "total": total_capacity, 
                    "start_iso": slot_start_iso, "end_iso": f"{date_str}T{slot['end']}:00", "status_msg": "Sẵn sàng"
                })
            return results
        except: return []

    def validate_and_create(self, data):
        try:
            if not self.booking_sheet: return False, "Lỗi kết nối Sheet DatPhong"
            booking_id = f"BK-{datetime.now().strftime('%y%m%d%H%M%S')}"
            auto_approve = self.get_auto_approval()
            initial_status = 'APPROVED' if auto_approve else 'PENDING'
            row = [
                booking_id, data.get('mssv'), data.get('user'), data.get('email'), 
                data.get('university'), data.get('phone'), data.get('type'), 
                data.get('lab_id'), data.get('lab_name'), data.get('start_time'), 
                data.get('end_time'), initial_status, data.get('purpose', ''), 
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data.get('group_size', 1), data.get('group_members', '')
            ]
            self.booking_sheet.append_row(row)
            return True, "Đăng ký thành công!"
        except Exception as e:
            return False, f"Lỗi ghi dữ liệu: {str(e)}"

    def update_booking_status(self, bid, status):
        try:
            if not self.booking_sheet: return False
            records = self.get_bookings()
            for idx, r in enumerate(records):
                if str(r.get('id', r.get('ID'))) == str(bid):
                    self.booking_sheet.update_cell(idx + 2, 12, status)
                    return True
            return False
        except: return False

    def add_hygiene_report(self, data):
        try:
            if not self.hygiene_sheet: return False, "Lỗi cấu hình Sheet"
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.get('lab_id'), data.get('lab_name'),
                data.get('reporter'), data.get('status'), data.get('notes'),
                data.get('image_url'), data.get('report_time')
            ]
            self.hygiene_sheet.append_row(row)
            return True, "Thành công!"
        except Exception as e: return False, str(e)

    def add_student(self, data):
        try:
            if not self.student_sheet: return False, "Lỗi kết nối Sheet SinhVien"
            # Khớp field từ student_register.html
            mssv = data.get('mssv')
            name = data.get('name') or data.get('user')
            email = data.get('email')
            s_class = data.get('class')
            major = data.get('major')
            purpose = data.get('purpose')
            
            row = [
                mssv, name, email, s_class, major, purpose, 
                'PENDING', datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            self.student_sheet.append_row(row)
            return True, "Gửi yêu cầu đăng ký thành công! Vui lòng chờ phê duyệt."
        except Exception as e: 
            return False, f"Lỗi: {str(e)}"

    def update_student_status(self, mssv, status):
        try:
            if not self.student_sheet: return False
            records = self.get_students()
            for idx, r in enumerate(records):
                if str(r.get('mssv', r.get('MSSV'))) == str(mssv):
                    self.student_sheet.update_cell(idx + 2, 6, status)
                    return True
            return False
        except: return False
