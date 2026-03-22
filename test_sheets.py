import os
import gspread
from google.oauth2.service_account import Credentials

def test_connection():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    cred_path = os.path.join(os.getcwd(), 'credentials.json')
    
    if not os.path.exists(cred_path):
        print("Error: credentials.json not found")
        return

    try:
        creds = Credentials.from_service_account_file(cred_path, scopes=scope)
        client = gspread.authorize(creds)
        sheet_id = '11TBgqd-LQfN3m35TKuN1d_psCZQQ6sFBlJ7vFrT4wko'
        sheet = client.open_by_key(sheet_id)
        print(f"Successfully opened sheet: {sheet.title}")
        
        worksheets = sheet.worksheets()
        print(f"Found {len(worksheets)} worksheets:")
        for ws in worksheets:
            print(f"- {ws.title} (ID: {ws.id})")
            
        required_names = ['DatPhong', 'DanhSachLab', 'SinhVien', 'VeSinh', 'GhiChu', 'CauHinh']
        for name in required_names:
            try:
                ws = sheet.worksheet(name)
                print(f"\nWorksheet: {name}")
                all_values = ws.get_all_values()
                if all_values:
                    print(f"  Headers: {all_values[0]}")
                    if len(all_values) > 1:
                        print(f"  First Record: {all_values[1]}")
                    else:
                        print("  No records found.")
                else:
                    print("  Worksheet is empty.")
            except Exception as e:
                print(f"\nWorksheet: {name} - Error: {str(e)}")

    except Exception as e:
        print(f"Connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection()
