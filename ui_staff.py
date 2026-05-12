import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from logic import DataManager

class StaffFrame(ctk.CTkFrame):
    def __init__(self, master, logout_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.logout_callback = logout_callback
        self.sort_by = "entry_date"
        self.sort_asc = False
        self.selected_ids = set()

        # Başlık ve Butonlar
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="PortLogix - Görevli Paneli", font=ctk.CTkFont(size=26, weight="bold", family="Helvetica"))
        self.title_label.pack(side="left")
        
        self.logout_btn = ctk.CTkButton(self.header_frame, text="Çıkış Yap", command=self.confirm_logout, width=100, fg_color="#c0392b", hover_color="#e74c3c")
        self.logout_btn.pack(side="right")
        
        self.archive_view_btn = ctk.CTkButton(self.header_frame, text="📦 Arşivi Gör", command=self.show_archive_window, width=120, fg_color="#7f8c8d", hover_color="#95a5a6")
        self.archive_view_btn.pack(side="right", padx=10)

        # İstatistikler & Rapor
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.stat_total = ctk.CTkLabel(self.stats_frame, text="Toplam: 0", font=ctk.CTkFont(weight="bold"), fg_color="#2c3e50", corner_radius=5, padx=10, pady=5)
        self.stat_total.pack(side="left", padx=(0, 10))
        
        self.stat_customs = ctk.CTkLabel(self.stats_frame, text="Gümrükte: 0", font=ctk.CTkFont(weight="bold"), fg_color="#f39c12", corner_radius=5, padx=10, pady=5)
        self.stat_customs.pack(side="left", padx=10)
        
        self.stat_ready = ctk.CTkLabel(self.stats_frame, text="Çıkışa Hazır: 0", font=ctk.CTkFont(weight="bold"), fg_color="#27ae60", corner_radius=5, padx=10, pady=5)
        self.stat_ready.pack(side="left", padx=10)
        
        self.export_btn = ctk.CTkButton(self.stats_frame, text="📊 Excel Rapor Al", command=self.export_to_excel, width=140, fg_color="#16a085", hover_color="#1abc9c", text_color="white")
        self.export_btn.pack(side="right")
        
        self.mass_archive_btn = ctk.CTkButton(self.stats_frame, text="🗑️ Seçilenleri Arşivle", command=self.mass_archive, width=150, fg_color="#d35400", hover_color="#e67e22", text_color="white", text_color_disabled="gray85")
        self.mass_archive_btn.pack(side="right", padx=10)
        self.mass_archive_btn.configure(state="disabled")

        # Sol form, sağ tablo
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # Form Alanı (Sol)
        self.form_frame = ctk.CTkFrame(self.content_frame, width=320)
        self.form_frame.pack(side="left", fill="y", padx=(0, 20))
        
        ctk.CTkLabel(self.form_frame, text="Yeni Kargo Ekle", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(15, 10))

        self.track_var = ctk.StringVar(value=DataManager.generate_tracking_number())
        
        def create_labeled_entry(parent, text, placeholder="", readonly=False, var=None):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(pady=2, padx=15, fill="x")
            ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=12)).pack(anchor="w")
            if readonly:
                entry = ctk.CTkEntry(frame, textvariable=var, state="readonly", fg_color=("gray85", "gray30"))
            else:
                var_str = ctk.StringVar()
                entry = ctk.CTkEntry(frame, placeholder_text=placeholder, textvariable=var_str)
                entry.var = var_str
            entry.pack(fill="x", ipady=2)
            return entry

        self.track_entry = create_labeled_entry(self.form_frame, "Takip Numarası:", readonly=True, var=self.track_var)
        self.plate_entry = create_labeled_entry(self.form_frame, "Plaka Numarası:", placeholder="(Örn: 34 ABC 123)")
        
        def format_plate(var, index, mode):
            val = self.plate_entry.var.get().upper()
            if self.plate_entry.var.get() != val:
                self.plate_entry.var.set(val)
        self.plate_entry.var.trace_add("write", format_plate)
        
        status_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        status_frame.pack(pady=2, padx=15, fill="x")
        ctk.CTkLabel(status_frame, text="Durum:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.status_option = ctk.CTkOptionMenu(status_frame, values=["Giriş Yaptı", "Gümrükte", "Elleçleniyor", "Çıkışa Hazır"])
        self.status_option.pack(fill="x", ipady=2)

        self.customs_entry = create_labeled_entry(self.form_frame, "Gümrük Maliyeti (₺):", placeholder="(Örn: 1500.00)")
        self.vat_entry = create_labeled_entry(self.form_frame, "KDV Tutarı (₺):", placeholder="(Oto Hesaplanır)")
        self.handling_entry = create_labeled_entry(self.form_frame, "Elleçleme Maliyeti (₺):", placeholder="(Örn: 250.00)")

        def validate_numeric(var_name, index, mode, entry_widget):
            text = entry_widget.var.get()
            cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
            if text != cleaned:
                entry_widget.var.set(cleaned)
                
            # Oto KDV %20
            if entry_widget == self.customs_entry and cleaned:
                try:
                    customs_val = float(cleaned)
                    self.vat_entry.var.set(f"{customs_val * 0.20:.2f}")
                except:
                    pass

        self.customs_entry.var.trace_add("write", lambda n, i, m: validate_numeric(n, i, m, self.customs_entry))
        self.vat_entry.var.trace_add("write", lambda n, i, m: validate_numeric(n, i, m, self.vat_entry))
        self.handling_entry.var.trace_add("write", lambda n, i, m: validate_numeric(n, i, m, self.handling_entry))

        btn_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        btn_frame.pack(pady=10, padx=15, fill="x")
        
        self.add_btn = ctk.CTkButton(btn_frame, text="➕ Kargo Ekle", command=self.add_shipment, font=ctk.CTkFont(weight="bold"), fg_color="#2980b9", hover_color="#3498db")
        self.add_btn.pack(fill="x", pady=5)
        
        self.clear_btn = ctk.CTkButton(btn_frame, text="🧹 Formu Temizle", command=self.clear_form, fg_color="transparent", border_width=1, hover_color="#34495e")
        self.clear_btn.pack(fill="x")

        # Pie Chart Area
        self.chart_frame = ctk.CTkFrame(self.form_frame, height=150, fg_color="transparent")
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sağ Alan (Arama + Tablo)
        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.search_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.search_frame.pack(fill="x", pady=(0, 10))
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Plaka veya Takip No Ara...", width=250)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list(search=self.search_entry.get()))

        # Tablo Başlıkları
        self.table_header = ctk.CTkFrame(self.right_frame, corner_radius=0, fg_color=("gray75", "#2c3e50"))
        self.table_header.pack(fill="x")
        
        # Checkbox başlığı için boşluk
        ctk.CTkLabel(self.table_header, text="✓", width=30).pack(side="left", padx=5)
        
        headers = [("Durum", "current_status", 150), ("Takip No", "tracking_number", 130), 
                   ("Plaka", "plate_number", 100), ("Giriş Tarihi", "entry_date", 150), ("İşlemler", None, 200)]
                   
        for text, col_name, width in headers:
            if col_name:
                btn = ctk.CTkButton(self.table_header, text=text, width=width, anchor="w", fg_color="transparent", 
                                    text_color=("black", "white"), font=ctk.CTkFont(weight="bold"),
                                    hover_color="#34495e", command=lambda c=col_name: self.set_sorting(c))
                btn.pack(side="left", padx=2, pady=2)
            else:
                ctk.CTkLabel(self.table_header, text=text, width=width, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2, pady=5)

        self.list_frame = ctk.CTkScrollableFrame(self.right_frame)
        self.list_frame.pack(fill="both", expand=True)
        
        self.refresh_list()

    def show_toast(self, message, success=True):
        color = "#2ecc71" if success else "#e74c3c"
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        # Sağ üst köşe
        x = self.winfo_screenwidth() - 320
        y = 50
        toast.geometry(f"300x50+{x}+{y}")
        
        frame = ctk.CTkFrame(toast, fg_color=color, corner_radius=10)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text=message, text_color="white", font=ctk.CTkFont(weight="bold", size=14)).pack(pady=10)
        
        self.after(2500, toast.destroy)

    def draw_pie_chart(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        stats = DataManager.get_statistics()
        total = stats['total']
        if total == 0: return
        
        sizes = [stats.get('entered', 0), stats.get('customs', 0), stats.get('handling', 0), stats.get('ready', 0)]
        labels = ['Giriş', 'Gümrük', 'Elleçleme', 'Hazır']
        colors = ['#3498db', '#f1c40f', '#e67e22', '#2ecc71']
        
        # Filtrele 0 olanları
        sizes_f, labels_f, colors_f = [], [], []
        for s, l, c in zip(sizes, labels, colors):
            if s > 0:
                sizes_f.append(s)
                labels_f.append(l)
                colors_f.append(c)

        fig = Figure(figsize=(3, 2), dpi=100)
        fig.patch.set_facecolor('#2b2b2b' if ctk.get_appearance_mode() == "Dark" else '#f0f0f0')
        
        ax = fig.add_subplot(111)
        ax.pie(sizes_f, labels=labels_f, colors=colors_f, startangle=90, textprops={'color':"w", 'fontsize':8})
        ax.axis('equal')
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def set_sorting(self, column):
        if self.sort_by == column:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_by = column
            self.sort_asc = True
        self.refresh_list(self.search_entry.get())

    def export_to_excel(self):
        df = DataManager.get_all_active_shipments()
        if df.empty:
            messagebox.showinfo("Rapor", "Aktarılacak aktif kargo bulunmamaktadır.")
            return
            
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = os.path.join(desktop_path, "Aktif_Kargolar.xlsx")
        try:
            df['entry_date'] = df['entry_date'].dt.strftime('%d.%m.%Y - %H:%M')
            export_df = df[['tracking_number', 'plate_number', 'current_status', 'entry_date', 'customs_cost', 'vat_cost', 'handling_cost']]
            export_df.columns = ["Takip No", "Plaka", "Durum", "Giriş Tarihi", "Gümrük Maliyeti", "KDV", "Elleçleme"]
            export_df.to_excel(filepath, index=False)
            self.show_toast("Excel Raporu Alındı!")
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulurken hata oluştu:\n{str(e)}")

    def update_stats(self):
        stats = DataManager.get_statistics()
        self.stat_total.configure(text=f"Toplam Kargo: {stats['total']}")
        self.stat_customs.configure(text=f"Gümrükte: {stats['customs']}")
        self.stat_ready.configure(text=f"Çıkışa Hazır: {stats['ready']}")
        self.draw_pie_chart()

    def confirm_logout(self):
        answer = messagebox.askyesno("Çıkış", "Çıkış yapmak istediğinize emin misiniz?")
        if answer:
            self.logout_callback()

    def add_shipment(self):
        try:
            customs = float(self.customs_entry.var.get() or 0.0)
            vat = float(self.vat_entry.var.get() or 0.0)
            handling = float(self.handling_entry.var.get() or 0.0)
            
            track = self.track_var.get()
            plate = self.plate_entry.var.get().strip()
            status = self.status_option.get()

            if not plate:
                self.show_toast("Plaka zorunludur!", success=False)
                return

            success, msg = DataManager.add_shipment(track, plate, status, customs, vat, handling)
            if success:
                self.show_toast("Kargo başarıyla eklendi!")
                self.clear_form()
                self.refresh_list()
                self.track_var.set(DataManager.generate_tracking_number())
            else:
                self.show_toast(msg, success=False)
                
        except ValueError:
            self.show_toast("Maliyetler sayısal olmalıdır!", success=False)

    def clear_form(self):
        self.plate_entry.var.set("")
        self.customs_entry.var.set("")
        self.vat_entry.var.set("")
        self.handling_entry.var.set("")
        self.status_option.set("Giriş Yaptı")

    def toggle_select(self, shipment_id, var):
        if var.get() == "on":
            self.selected_ids.add(shipment_id)
        else:
            self.selected_ids.discard(shipment_id)
            
        if self.selected_ids:
            self.mass_archive_btn.configure(state="normal")
        else:
            self.mass_archive_btn.configure(state="disabled")

    def mass_archive(self):
        if not self.selected_ids: return
        answer = messagebox.askyesno("Toplu Arşiv", f"Seçilen {len(self.selected_ids)} kargoyu arşivlemek istiyor musunuz?")
        if answer:
            for sid in self.selected_ids:
                DataManager.archive_shipment(sid)
            self.selected_ids.clear()
            self.mass_archive_btn.configure(state="disabled")
            self.refresh_list(self.search_entry.get())
            self.show_toast("Seçilenler arşivlendi!")

    def get_status_color(self, status):
        if status == "Giriş Yaptı": return "🔵"
        if status == "Gümrükte": return "🟡"
        if status == "Elleçleniyor": return "🟠"
        if status == "Çıkışa Hazır": return "🟢"
        return "⚪"

    def refresh_list(self, search=""):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        if search:
            df = DataManager.search_active_shipments(search)
        else:
            df = DataManager.get_all_active_shipments()
            
        self.update_stats()

        if df.empty:
            ctk.CTkLabel(self.list_frame, text="Şu an takip edilen kargo bulunmamaktadır.", font=ctk.CTkFont(size=16, slant="italic")).pack(pady=40)
            return
            
        if self.sort_by in df.columns:
            df = df.sort_values(by=self.sort_by, ascending=self.sort_asc)

        for idx, (index, row) in enumerate(df.iterrows()):
            zebra_bg = ("gray90", "#1e1e2f") if idx % 2 == 0 else ("gray85", "#252536")
            bg_color = ("#ffcccc", "#4a1c1c") if row.get('is_critical', False) else zebra_bg
            text_col = "black" if row.get('is_critical', False) and ctk.get_appearance_mode()=="Light" else "white"
            
            row_frame = ctk.CTkFrame(self.list_frame, fg_color=bg_color, corner_radius=0)
            row_frame.pack(fill="x", pady=1)
            
            # Checkbox
            chk_var = ctk.StringVar(value="on" if row['id'] in self.selected_ids else "off")
            chk = ctk.CTkCheckBox(row_frame, text="", variable=chk_var, onvalue="on", offvalue="off", width=30, 
                                  command=lambda id=row['id'], v=chk_var: self.toggle_select(id, v))
            chk.pack(side="left", padx=5)
            
            status_icon = self.get_status_color(row['current_status'])
            ctk.CTkLabel(row_frame, text=f"{status_icon} {row['current_status']}", width=150, anchor="w", text_color=text_col).pack(side="left", padx=2, pady=5)
            ctk.CTkLabel(row_frame, text=row['tracking_number'], width=130, anchor="w", text_color=text_col).pack(side="left", padx=2, pady=5)
            ctk.CTkLabel(row_frame, text=row['plate_number'], width=100, anchor="w", text_color=text_col).pack(side="left", padx=2, pady=5)
            
            date_str = row['entry_date'].strftime('%d.%m.%Y - %H:%M') if hasattr(row['entry_date'], 'strftime') else str(row['entry_date']).split('.')[0]
            ctk.CTkLabel(row_frame, text=date_str, width=150, anchor="w", text_color=text_col).pack(side="left", padx=2, pady=5)
            
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.pack(side="left", padx=5, pady=5, fill="x", expand=True)
            
            status_opt = ctk.CTkOptionMenu(actions_frame, values=["Giriş Yaptı", "Gümrükte", "Elleçleniyor", "Çıkışa Hazır"], width=110)
            status_opt.set(row['current_status'])
            status_opt.pack(side="left", padx=2)
            
            update_btn = ctk.CTkButton(actions_frame, text="✏️", width=30, fg_color="#2980b9", command=lambda id=row['id'], opt=status_opt: self.update_status(id, opt.get()))
            update_btn.pack(side="left", padx=2)
            
            archive_btn = ctk.CTkButton(actions_frame, text="📦", width=30, fg_color="#d35400", hover_color="#e67e22", command=lambda id=row['id']: self.confirm_archive(id))
            archive_btn.pack(side="left", padx=2)
            
            copy_btn = ctk.CTkButton(actions_frame, text="📋", width=30, fg_color="#7f8c8d", hover_color="#95a5a6", command=lambda t=row['tracking_number']: self.copy_tracking(t))
            copy_btn.pack(side="left", padx=2)
            
            delete_btn = ctk.CTkButton(actions_frame, text="🗑️", width=30, fg_color="#c0392b", hover_color="#e74c3c", command=lambda id=row['id']: self.confirm_delete(id))
            delete_btn.pack(side="left", padx=2)

    def update_status(self, shipment_id, new_status):
        DataManager.update_shipment_status(shipment_id, new_status)
        self.show_toast("Durum güncellendi!")
        self.refresh_list(self.search_entry.get())

    def confirm_archive(self, shipment_id):
        answer = messagebox.askyesno("Arşivle", "Bu kargoyu arşive taşımak istiyor musunuz?")
        if answer:
            DataManager.archive_shipment(shipment_id)
            self.show_toast("Kargo arşivlendi!")
            self.refresh_list(self.search_entry.get())

    def confirm_delete(self, shipment_id, refresh_callback=None):
        answer = messagebox.askyesno("Kalıcı Olarak Sil", "Bu kargoyu tamamen silmek istediğinize emin misiniz? Bu işlem geri alınamaz!")
        if answer:
            DataManager.delete_shipment(shipment_id)
            self.show_toast("Kargo başarıyla silindi!")
            if refresh_callback:
                refresh_callback()
            else:
                self.refresh_list(self.search_entry.get())

    def copy_tracking(self, tracking_num):
        self.clipboard_clear()
        self.clipboard_append(tracking_num)
        self.show_toast("Takip numarası kopyalandı!")

    def show_archive_window(self):
        archive_win = ctk.CTkToplevel(self)
        archive_win.title("Arşivlenmiş Kargolar")
        archive_win.geometry("800x600")
        archive_win.attributes("-topmost", True)
        
        search_frame = ctk.CTkFrame(archive_win, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Plaka veya Takip No Ara...", width=250)
        search_entry.pack(side="left")
        
        scroll_frame = ctk.CTkScrollableFrame(archive_win)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        def unarchive_callback(shipment_id):
            DataManager.unarchive_shipment(shipment_id)
            self.show_toast("Kargo arşivden çıkarıldı!")
            refresh_archive(search_entry.get())
            self.refresh_list()

        def refresh_archive(keyword=""):
            for widget in scroll_frame.winfo_children():
                widget.destroy()
                
            df = DataManager.get_archived_shipments(keyword)
            if df.empty:
                ctk.CTkLabel(scroll_frame, text="Arşivde eşleşen kargo bulunmuyor.", font=ctk.CTkFont(size=16)).pack(pady=40)
                return
                
            for index, row in df.iterrows():
                card = ctk.CTkFrame(scroll_frame, fg_color=("gray85", "gray20"), corner_radius=10)
                card.pack(fill="x", pady=5)
                
                date_str = str(row['last_update']).split('.')[0]
                info = f"📦 Takip No: {row['tracking_number']} | Plaka: {row['plate_number']} | Arşivlenme: {date_str}"
                ctk.CTkLabel(card, text=info, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)
                
                delete_btn = ctk.CTkButton(card, text="🗑️ Sil", width=60, fg_color="#c0392b", hover_color="#e74c3c", command=lambda id=row['id']: self.confirm_delete(id, refresh_callback=lambda: refresh_archive(search_entry.get())))
                delete_btn.pack(side="right", padx=5, pady=10)
                
                unarch_btn = ctk.CTkButton(card, text="♻️ Çıkar", width=70, fg_color="#27ae60", hover_color="#2ecc71", command=lambda id=row['id']: unarchive_callback(id))
                unarch_btn.pack(side="right", padx=5, pady=10)
                
                copy_btn = ctk.CTkButton(card, text="📋 Kopyala", width=70, fg_color="#7f8c8d", hover_color="#95a5a6", command=lambda t=row['tracking_number']: self.copy_tracking(t))
                copy_btn.pack(side="right", padx=5, pady=10)

        search_entry.bind("<KeyRelease>", lambda e: refresh_archive(search_entry.get()))
        refresh_archive()
