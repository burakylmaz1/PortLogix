import sqlite3
import pandas as pd
from datetime import datetime
import random
import string
from database import get_connection

class Helper:
    @staticmethod
    def format_currency(value: float) -> str:
        """Sayıyı Türk Lirası formatına çevirir: 14.500,00 ₺"""
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"

    @staticmethod
    def calculate_wait_time(entry_date_str: str) -> str:
        """Giriş tarihinden bugüne kadar geçen süreyi hesaplar"""
        try:
            if isinstance(entry_date_str, str):
                entry_date_str = entry_date_str.split('.')[0]
                entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d %H:%M:%S')
            else:
                entry_date = entry_date_str

            now = datetime.now()
            diff = now - entry_date
            
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            
            if days > 0:
                return f"{days} Gün {hours} Saat"
            return f"{hours} Saat"
        except Exception:
            return "Bilinmiyor"

    @staticmethod
    def generate_qr_code(data: str, filename: str):
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filename)
        return filename

class LandedCostCalculator:
    @staticmethod
    def calculate_total(customs: float, vat: float, handling: float) -> float:
        return float(customs) + float(vat) + float(handling)

class DataManager:
    @staticmethod
    def generate_tracking_number():
        """PLX- YılAyGün - Rastgele4HarfRakam formatında takip no üretir."""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"PLX-{date_str}-{random_str}"

    @staticmethod
    def get_all_active_shipments():
        conn = get_connection()
        query = "SELECT id, tracking_number, plate_number, entry_date, current_status, customs_cost, vat_cost, handling_cost FROM shipments WHERE is_archived = 0 ORDER BY entry_date DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['entry_date'] = pd.to_datetime(df['entry_date'])
            now = datetime.now()
            df['is_critical'] = (now - df['entry_date']).dt.days > 3
        
        return df

    @staticmethod
    def get_archived_shipments(keyword=""):
        conn = get_connection()
        if keyword:
            query = f"SELECT id, tracking_number, plate_number, entry_date, last_update, current_status, customs_cost, vat_cost, handling_cost FROM shipments WHERE is_archived = 1 AND (tracking_number LIKE '%{keyword}%' OR plate_number LIKE '%{keyword}%') ORDER BY last_update DESC"
        else:
            query = "SELECT id, tracking_number, plate_number, entry_date, last_update, current_status, customs_cost, vat_cost, handling_cost FROM shipments WHERE is_archived = 1 ORDER BY last_update DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    @staticmethod
    def get_statistics():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE is_archived = 0")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE is_archived = 0 AND current_status = 'Giriş Yaptı'")
        entered = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE is_archived = 0 AND current_status = 'Gümrükte'")
        customs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE is_archived = 0 AND current_status = 'Elleçleniyor'")
        handling = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE is_archived = 0 AND current_status = 'Çıkışa Hazır'")
        ready = cursor.fetchone()[0]
        
        conn.close()
        return {"total": total, "entered": entered, "customs": customs, "handling": handling, "ready": ready}

    @staticmethod
    def search_active_shipments(keyword: str):
        conn = get_connection()
        query = f"SELECT id, tracking_number, plate_number, entry_date, current_status FROM shipments WHERE is_archived = 0 AND (tracking_number LIKE '%{keyword}%' OR plate_number LIKE '%{keyword}%') ORDER BY entry_date DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if not df.empty:
            df['entry_date'] = pd.to_datetime(df['entry_date'])
            now = datetime.now()
            df['is_critical'] = (now - df['entry_date']).dt.days > 3
        return df

    @staticmethod
    def get_shipment_by_tracking(tracking_number: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shipments WHERE tracking_number = ?", (tracking_number,))
        row = cursor.fetchone()
        
        if row:
            columns = [col[0] for col in cursor.description]
            shipment = dict(zip(columns, row))
            conn.close()
            return shipment
        
        conn.close()
        return None

    @staticmethod
    def log_action(action, details):
        import os
        from datetime import datetime
        log_file = "log.txt"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{now_str}] {action} | {details}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)

    @staticmethod
    def add_shipment(tracking_number, plate_number, status, customs, vat, handling):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO shipments (tracking_number, plate_number, current_status, customs_cost, vat_cost, handling_cost)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tracking_number, plate_number, status, customs, vat, handling))
            conn.commit()
            DataManager.log_action("EKLEME", f"Takip No: {tracking_number}, Plaka: {plate_number}")
            return True, "Kayıt başarıyla eklendi."
        except sqlite3.IntegrityError:
            return False, "Bu takip numarası zaten mevcut."
        finally:
            conn.close()

    @staticmethod
    def update_shipment_status(shipment_id, new_status):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE shipments 
            SET current_status = ?, last_update = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, shipment_id))
        conn.commit()
        conn.close()
        DataManager.log_action("GÜNCELLEME", f"ID: {shipment_id} durumu {new_status} yapıldı.")

    @staticmethod
    def archive_shipment(shipment_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE shipments SET is_archived = 1, last_update = CURRENT_TIMESTAMP WHERE id = ?", (shipment_id,))
        conn.commit()
        conn.close()
        DataManager.log_action("ARŞİVLEME", f"ID: {shipment_id} arşive taşındı.")

    @staticmethod
    def unarchive_shipment(shipment_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE shipments SET is_archived = 0, last_update = CURRENT_TIMESTAMP WHERE id = ?", (shipment_id,))
        conn.commit()
        conn.close()
        DataManager.log_action("ARŞİVDEN ÇIKARMA", f"ID: {shipment_id} arşivden çıkarıldı.")

    @staticmethod
    def delete_shipment(shipment_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shipments WHERE id = ?", (shipment_id,))
        conn.commit()
        conn.close()
        DataManager.log_action("SİLME", f"ID: {shipment_id} kalıcı olarak silindi.")

    @staticmethod
    def verify_login(username, password):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None
