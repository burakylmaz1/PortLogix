import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import os
from fpdf import FPDF
from logic import DataManager, LandedCostCalculator, Helper

class CustomerAnimatedBackground(ctk.CTkCanvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, highlightthickness=0, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.width = 1000
        self.height = 700
        
        self.blobs = [
            [200, 200, 300, 2, 1.5, "#1a0b2e", "#100620"], 
            [800, 500, 400, -1.5, -2, "#0a192f", "#050c1a"], 
            [500, 100, 350, 1, -1, "#17202A", "#0e131a"], 
            [100, 600, 250, -2, 1, "#0f2027", "#081115"]
        ]
        self.animate()

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        
    def animate(self):
        self.delete("all")
        self.configure(bg="#050505")
        
        for blob in self.blobs:
            if blob[0] - blob[2] < -200 or blob[0] + blob[2] > self.width + 200:
                blob[3] *= -1
            if blob[1] - blob[2] < -200 or blob[1] + blob[2] > self.height + 200:
                blob[4] *= -1
                
            blob[0] += blob[3]
            blob[1] += blob[4]
            
            x, y, r, glow_color, core_color = blob[0], blob[1], blob[2], blob[5], blob[6]
            self.create_oval(x-r-30, y-r-30, x+r+30, y+r+30, fill=glow_color, outline="")
            self.create_oval(x-r, y-r, x+r, y+r, fill=core_color, outline="")
            
        self.anim_id = self.after(50, self.animate)
        
    def stop(self):
        try: self.after_cancel(self.anim_id)
        except: pass

class CustomerFrame(ctk.CTkFrame):
    def __init__(self, master, logout_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.logout_callback = logout_callback
        self.current_shipment_data = None
        self.recent_searches = []
        self.lang = "TR"

        # Dinamik Arkaplan
        self.bg_canvas = CustomerAnimatedBackground(self)
        self.bg_canvas.place(relwidth=1, relheight=1)

        # Container for content so it stays above canvas
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.place(relwidth=1, relheight=1)

        self.header_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=20)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="PortLogix - Kargo Takip", font=ctk.CTkFont(size=26, weight="bold", family="Helvetica"))
        self.title_label.pack(side="left")
        
        self.lang_btn = ctk.CTkButton(self.header_frame, text="🇹🇷 TR", width=50, fg_color="transparent", border_width=1, command=self.toggle_lang)
        self.lang_btn.pack(side="right", padx=10)
        
        # Geri Dön butonu kurumsal renk
        self.logout_btn = ctk.CTkButton(self.header_frame, text="Geri Dön", command=self.do_logout, width=100, fg_color="#34495e", hover_color="#2c3e50")
        self.logout_btn.pack(side="right")

        self.search_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.search_frame.pack(pady=10)
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Takip Numarası Girin (Örn: PLX-...).", width=350, height=45, font=ctk.CTkFont(size=16))
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<Return>", lambda e: self.search_shipment())
        
        # Search butonu kurumsal renk
        self.search_btn = ctk.CTkButton(self.search_frame, text="Sorgula", font=ctk.CTkFont(size=16, weight="bold"), height=45, command=self.search_shipment, fg_color="#2980b9", hover_color="#3498db")
        self.search_btn.pack(side="left")

        self.recent_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.recent_frame.pack(pady=5)
        self.recent_lbl = ctk.CTkLabel(self.recent_frame, text="Son Sorgulananlar:", text_color="gray")
        self.recent_lbl.pack(side="left", padx=5)

        self.result_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Empty State / Error Area
        self.empty_state = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        self.empty_state.pack(fill="both", expand=True)
        self.empty_icon = ctk.CTkLabel(self.empty_state, text="🚢", font=ctk.CTkFont(size=72))
        self.empty_icon.pack(pady=(40, 10))
        self.empty_text = ctk.CTkLabel(self.empty_state, text="Kargo Sorgulamak İçin Takip Numarası Girin", font=ctk.CTkFont(size=18), text_color="gray")
        self.empty_text.pack()

        # Ana Kart
        self.card_frame = ctk.CTkFrame(self.result_frame, corner_radius=20, fg_color=("gray85", "#1c1c24"), border_width=1, border_color="#34495e")
        
        self.top_info = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.top_info.pack(fill="x", padx=20, pady=(20, 0))
        self.wait_lbl = ctk.CTkLabel(self.top_info, text="", font=ctk.CTkFont(size=16), text_color="#e67e22")
        self.wait_lbl.pack(side="left")
        self.eta_lbl = ctk.CTkLabel(self.top_info, text="", font=ctk.CTkFont(size=16, slant="italic"), text_color="#3498db")
        self.eta_lbl.pack(side="left", padx=20)

        self.status_label = ctk.CTkLabel(self.card_frame, text="", font=ctk.CTkFont(size=24, weight="bold"))
        self.status_label.pack(pady=(15, 5))
        
        self.progress_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.progress_frame.pack(pady=10, fill="x", padx=50)
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=18)
        self.progress_bar.pack(fill="x")
        self.steps_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.steps_frame.pack(fill="x", pady=5)
        self.step1 = ctk.CTkLabel(self.steps_frame, text="📥 Giriş Yaptı", font=ctk.CTkFont(size=13))
        self.step1.pack(side="left", expand=True)
        self.step2 = ctk.CTkLabel(self.steps_frame, text="🏢 Gümrükte", font=ctk.CTkFont(size=13))
        self.step2.pack(side="left", expand=True)
        self.step3 = ctk.CTkLabel(self.steps_frame, text="⚙️ Elleçleniyor", font=ctk.CTkFont(size=13))
        self.step3.pack(side="left", expand=True)
        self.step4 = ctk.CTkLabel(self.steps_frame, text="✅ Çıkışa Hazır", font=ctk.CTkFont(size=13))
        self.step4.pack(side="left", expand=True)

        self.grid_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.grid_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.grid_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Sol Kart (Plaka + QR Code Gömülü)
        self.left_card = ctk.CTkFrame(self.grid_frame, fg_color=("gray90", "#2b2b36"), corner_radius=10)
        self.left_card.grid(row=0, column=0, padx=(0, 15), pady=5, sticky="nsew")
        ctk.CTkLabel(self.left_card, text="🚚 Plaka", font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(10, 0))
        self.plate_lbl = ctk.CTkLabel(self.left_card, text="", font=ctk.CTkFont(size=20, weight="bold"))
        self.plate_lbl.pack()
        ctk.CTkLabel(self.left_card, text="📅 Giriş Tarihi", font=ctk.CTkFont(size=14), text_color="gray").pack(pady=(10, 0))
        self.date_lbl = ctk.CTkLabel(self.left_card, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self.date_lbl.pack()
        
        # Gömülü QR Kod
        self.qr_label = ctk.CTkLabel(self.left_card, text="")
        self.qr_label.pack(pady=10)

        # Orta Kart (Maliyetler)
        self.mid_card = ctk.CTkFrame(self.grid_frame, fg_color=("gray90", "#2b2b36"), corner_radius=10)
        self.mid_card.grid(row=0, column=1, padx=15, pady=5, sticky="nsew")
        ctk.CTkLabel(self.mid_card, text="Maliyet Detayları", font=ctk.CTkFont(size=14, weight="bold"), text_color="gray").pack(pady=5)
        
        def create_cost_row(parent):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=5)
            lbl = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=14))
            lbl.pack(side="left")
            val = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=14, weight="bold"))
            val.pack(side="right")
            return lbl, val
            
        self.c_lbl_title, self.c_lbl_val = create_cost_row(self.mid_card)
        self.v_lbl_title, self.v_lbl_val = create_cost_row(self.mid_card)
        self.h_lbl_title, self.h_lbl_val = create_cost_row(self.mid_card)

        # Sağ Kart (Toplam)
        self.right_card = ctk.CTkFrame(self.grid_frame, fg_color=("#d5f5e3", "#145a32"), corner_radius=10)
        self.right_card.grid(row=0, column=2, padx=(15, 0), pady=5, sticky="nsew")
        ctk.CTkLabel(self.right_card, text="TOPLAM TUTAR", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(30, 5))
        self.total_lbl = ctk.CTkLabel(self.right_card, text="", font=ctk.CTkFont(size=30, weight="bold"))
        self.total_lbl.pack(pady=10)

        # Alt Kısım
        self.bottom_info = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.bottom_info.pack(fill="x", padx=20, pady=(0, 15))
        self.receipt_btn = ctk.CTkButton(self.bottom_info, text="📄 PDF Makbuz İndir", font=ctk.CTkFont(weight="bold", size=14), command=self.download_pdf, fg_color="#8e44ad", hover_color="#9b59b6", height=40)
        self.receipt_btn.pack(side="left", expand=True)
        self.update_time_lbl = ctk.CTkLabel(self.bottom_info, text="", text_color="gray", font=ctk.CTkFont(size=12, slant="italic"))
        self.update_time_lbl.pack(side="right")

    def do_logout(self):
        self.bg_canvas.stop()
        self.logout_callback()

    def toggle_lang(self):
        if self.lang == "TR":
            self.lang = "EN"
            self.lang_btn.configure(text="🇬🇧 EN")
            self.title_label.configure(text="PortLogix - Shipment Tracking")
            self.search_btn.configure(text="Search")
            self.search_entry.configure(placeholder_text="Enter Tracking Number...")
            self.recent_lbl.configure(text="Recent Searches:")
            self.empty_text.configure(text="Enter a Tracking Number to Search")
            self.receipt_btn.configure(text="📄 Download PDF Receipt")
        else:
            self.lang = "TR"
            self.lang_btn.configure(text="🇹🇷 TR")
            self.title_label.configure(text="PortLogix - Kargo Takip")
            self.search_btn.configure(text="Sorgula")
            self.search_entry.configure(placeholder_text="Takip Numarası Girin (Örn: PLX-...).")
            self.recent_lbl.configure(text="Son Sorgulananlar:")
            self.empty_text.configure(text="Kargo Sorgulamak İçin Takip Numarası Girin")
            self.receipt_btn.configure(text="📄 PDF Makbuz İndir")

    def update_recent_searches(self, tracking_num):
        if tracking_num not in self.recent_searches:
            self.recent_searches.insert(0, tracking_num)
            if len(self.recent_searches) > 3:
                self.recent_searches.pop()
        
        for widget in self.recent_frame.winfo_children():
            if widget != self.recent_lbl:
                widget.destroy()
                
        for tk_num in self.recent_searches:
            # Chip görünümü
            btn = ctk.CTkButton(self.recent_frame, text=tk_num, width=80, height=25, fg_color="#34495e", text_color="white", corner_radius=12, command=lambda num=tk_num: self.quick_search(num))
            btn.pack(side="left", padx=5)

    def quick_search(self, num):
        self.search_entry.delete(0, 'end')
        self.search_entry.insert(0, num)
        self.search_shipment()

    def search_shipment(self):
        tracking_num = self.search_entry.get().strip()
        msg_not_found = "Kayıt bulunamadı!" if self.lang == "TR" else "Record not found!"
        
        self.card_frame.pack_forget()
        self.empty_state.pack(fill="both", expand=True)

        if not tracking_num:
            self.empty_icon.configure(text="⚠️")
            self.empty_text.configure(text="Lütfen takip numarası girin!" if self.lang=="TR" else "Please enter tracking number!")
            return

        shipment = DataManager.get_shipment_by_tracking(tracking_num)

        if not shipment:
            self.empty_icon.configure(text="📦 ❌")
            self.empty_text.configure(text=msg_not_found)
        else:
            self.empty_state.pack_forget()
            self.current_shipment_data = shipment
            self.update_recent_searches(tracking_num)
            self.prepare_card_data(shipment)
            self.animate_card_reveal()

    def animate_card_reveal(self):
        # Yavaşça belirmeyi simüle etmek için şelale (waterfall) gösterimi
        self.card_frame.pack(fill="both", expand=True, padx=40, pady=10)
        widgets_to_reveal = [self.top_info, self.status_label, self.progress_frame, self.grid_frame, self.bottom_info]
        
        for w in widgets_to_reveal:
            w.pack_forget()
            
        def reveal(idx):
            if idx < len(widgets_to_reveal):
                # Orijinal pack parametrelerini korumak için
                w = widgets_to_reveal[idx]
                if w == self.grid_frame:
                    w.pack(pady=20, padx=20, fill="both", expand=True)
                elif w == self.progress_frame:
                    w.pack(pady=10, fill="x", padx=50)
                elif w == self.top_info:
                    w.pack(fill="x", padx=20, pady=(20, 0))
                elif w == self.bottom_info:
                    w.pack(fill="x", padx=20, pady=(0, 15))
                else:
                    w.pack(pady=(15, 5))
                self.after(80, lambda: reveal(idx+1))
                
        reveal(0)

    def prepare_card_data(self, shipment):
        self.plate_lbl.configure(text=shipment['plate_number'])
        date_str = str(shipment['entry_date']).split('.')[0]
        self.date_lbl.configure(text=date_str)
        
        wait_time = Helper.calculate_wait_time(shipment['entry_date'])
        self.wait_lbl.configure(text=f"⏱ Bekleme: {wait_time}")
        
        import datetime
        now = datetime.datetime.now()
        lu = shipment.get('last_update', shipment['entry_date'])
        if isinstance(lu, str):
            try: lu = datetime.datetime.strptime(lu.split('.')[0], '%Y-%m-%d %H:%M:%S')
            except: lu = now
        diff_mins = max(0, int((now - lu).total_seconds() / 60))
        self.update_time_lbl.configure(text=f"Son Güncelleme: {diff_mins} dakika önce")
        
        # Gömülü QR
        total = LandedCostCalculator.calculate_total(shipment['customs_cost'], shipment['vat_cost'], shipment['handling_cost'])
        data = f"Takip: {shipment['tracking_number']}\nPlaka: {shipment['plate_number']}\nToplam: {total} TL"
        fn = "temp_qr.png"
        Helper.generate_qr_code(data, fn)
        img = ctk.CTkImage(Image.open(fn), size=(100, 100))
        self.qr_label.configure(image=img)
        self.qr_label.image = img
        
        status = shipment['current_status']
        status_map = {
            "Giriş Yaptı": (0.25, "#3498db", "Tahmini Süre: 2 Gün"),
            "Gümrükte": (0.50, "#f1c40f", "Tahmini Süre: 1 Gün"),
            "Elleçleniyor": (0.75, "#e67e22", "Tahmini Süre: 4 Saat"),
            "Çıkışa Hazır": (1.0, "#2ecc71", "Tamamlandı")
        }
        
        prog_val, prog_color, eta = status_map.get(status, (0, "blue", ""))
        self.progress_bar.set(prog_val)
        self.progress_bar.configure(progress_color=prog_color)
        
        self.eta_lbl.configure(text=eta)
        self.card_frame.configure(border_color=prog_color)
        self.status_label.configure(text=status.upper(), text_color=prog_color)
        
        colors = ["gray" if prog_val < 0.25 else "white",
                  "gray" if prog_val < 0.50 else "white",
                  "gray" if prog_val < 0.75 else "white",
                  "gray" if prog_val < 1.0 else "white"]
                  
        if ctk.get_appearance_mode() == "Light":
            colors = ["gray" if c == "gray" else "black" for c in colors]

        self.step1.configure(text_color=colors[0])
        self.step2.configure(text_color=colors[1])
        self.step3.configure(text_color=colors[2])
        self.step4.configure(text_color=colors[3])

        customs = shipment['customs_cost']
        vat = shipment['vat_cost']
        handling = shipment['handling_cost']
        total_cost = LandedCostCalculator.calculate_total(customs, vat, handling)

        self.c_lbl_title.configure(text="🏢 Gümrük:")
        self.c_lbl_val.configure(text=Helper.format_currency(customs))
        self.v_lbl_title.configure(text="🧾 KDV:")
        self.v_lbl_val.configure(text=Helper.format_currency(vat))
        self.h_lbl_title.configure(text="⚙️ Elleçleme:")
        self.h_lbl_val.configure(text=Helper.format_currency(handling))
        self.total_lbl.configure(text=Helper.format_currency(total_cost))

    def download_pdf(self):
        if not self.current_shipment_data: return
        shipment = self.current_shipment_data
        filename = f"Makbuz_{shipment['tracking_number']}.pdf"
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = os.path.join(desktop_path, filename)
        
        customs = shipment['customs_cost']
        vat = shipment['vat_cost']
        handling = shipment['handling_cost']
        total_cost = LandedCostCalculator.calculate_total(customs, vat, handling)
        
        try:
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font("Arial", 'B', 24)
            pdf.cell(200, 20, txt="PORTLOGIX - TAHSILAT MAKBUZU", ln=True, align='C')
            
            pdf.set_font("Arial", '', 12)
            pdf.cell(200, 10, txt="-"*50, ln=True, align='C')
            
            pdf.cell(100, 10, txt=f"Takip Numarasi : {shipment['tracking_number']}", ln=False)
            pdf.cell(100, 10, txt=f"Plaka Numarasi : {shipment['plate_number']}", ln=True)
            
            date_str = str(shipment['entry_date']).split('.')[0]
            pdf.cell(100, 10, txt=f"Giris Tarihi   : {date_str}", ln=False)
            
            # TR karakter donusumu
            tr_map = str.maketrans("ıişğüöçIİŞĞÜÖÇ", "iisguocIISGUOC")
            status_text = str(shipment['current_status']).translate(tr_map)
            pdf.cell(100, 10, txt=f"Mevcut Durum   : {status_text}", ln=True)
            
            pdf.cell(200, 10, txt="-"*50, ln=True, align='C')
            
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Maliyet Detaylari", ln=True)
            pdf.set_font("Arial", '', 12)
            
            pdf.cell(150, 10, txt="Gumruk Maliyeti:", ln=False)
            pdf.cell(50, 10, txt=f"{customs:,.2f} TL", ln=True, align='R')
            
            pdf.cell(150, 10, txt="KDV Tutari:", ln=False)
            pdf.cell(50, 10, txt=f"{vat:,.2f} TL", ln=True, align='R')
            
            pdf.cell(150, 10, txt="Ellecleme Gideri:", ln=False)
            pdf.cell(50, 10, txt=f"{handling:,.2f} TL", ln=True, align='R')
            
            pdf.cell(200, 5, txt="", ln=True)
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(150, 10, txt="TOPLAM TUTAR:", ln=False)
            pdf.cell(50, 10, txt=f"{total_cost:,.2f} TL", ln=True, align='R')
            
            pdf.output(filepath)
            messagebox.showinfo("Basarili", f"PDF Makbuz masaustune kaydedildi:\n{filename}")
        except Exception as e:
            messagebox.showerror("Hata", f"PDF oluşturulurken hata oluştu:\n{str(e)}\n\n(Not: Türkçe karakter hatası olabilir, Arial fontu desteklemiyor olabilir.)")
