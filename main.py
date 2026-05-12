import customtkinter as ctk
import math
import ctypes
from logic import DataManager
from ui_staff import StaffFrame
from ui_customer import CustomerFrame

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AnimatedBackground(ctk.CTkCanvas):
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
            
            # Glow effect (larger, slightly different color)
            self.create_oval(x-r-30, y-r-30, x+r+30, y+r+30, fill=glow_color, outline="")
            # Core
            self.create_oval(x-r, y-r, x+r, y+r, fill=core_color, outline="")
            
        self.after(50, self.animate)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PortLogix V4 - Liman Otomasyon Sistemi")
        self.geometry("1000x700")
        self.minsize(900, 600)

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.current_frame = None

        self.show_login_frame()

    def clear_container(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    def show_login_frame(self):
        self.clear_container()

        self.current_frame = ctk.CTkFrame(self.container)
        self.current_frame.pack(fill="both", expand=True)

        self.bg_canvas = AnimatedBackground(self.current_frame)
        self.bg_canvas.place(relwidth=1, relheight=1)
        
        # Müşteri Paneli Outline Button
        customer_btn = ctk.CTkButton(self.current_frame, text="Müşteri Paneli", font=ctk.CTkFont(weight="bold"), 
                                     command=self.show_customer_frame, fg_color="transparent", border_width=2, 
                                     border_color="#3498db", hover_color="#1a5276", text_color="#3498db", width=150)
        customer_btn.place(relx=0.95, rely=0.05, anchor="ne")

        # Glassmorphism benzeri ince şeffafımsı kenarlık
        self.login_card = ctk.CTkFrame(self.current_frame, width=400, height=520, corner_radius=25, fg_color="#1e1e2f", border_width=1, border_color="#3a3a4f")
        self.login_card.place(relx=0.5, rely=0.5, anchor="center")
        self.login_card.bind("<Button-1>", lambda e: "break")

        title = ctk.CTkLabel(self.login_card, text="PORTLOGIX", font=ctk.CTkFont(size=36, weight="bold", family="Helvetica"), text_color="#ecf0f1")
        title.pack(pady=(40, 5))
        
        self.welcome_lbl = ctk.CTkLabel(self.login_card, text="Liman Operasyon Sistemi", font=ctk.CTkFont(size=14), text_color="#95a5a6")
        self.welcome_lbl.pack(pady=(0, 20))

        user_frame = ctk.CTkFrame(self.login_card, fg_color="transparent")
        user_frame.pack(pady=10)
        ctk.CTkLabel(user_frame, text="👤", font=ctk.CTkFont(size=18)).pack(side="left", padx=(0, 5))
        self.user_entry = ctk.CTkEntry(user_frame, placeholder_text="Kullanıcı Adı", width=250, height=45)
        self.user_entry.pack(side="left")
        
        # Focus event for welcome message
        self.user_entry.bind("<FocusIn>", lambda e: self.welcome_lbl.configure(text="Sisteme Hoşgeldiniz", text_color="#2ecc71"))
        self.user_entry.bind("<FocusOut>", lambda e: self.welcome_lbl.configure(text="Liman Operasyon Sistemi", text_color="#95a5a6"))

        pass_wrapper = ctk.CTkFrame(self.login_card, fg_color="transparent")
        pass_wrapper.pack(pady=10)
        ctk.CTkLabel(pass_wrapper, text="🔒", font=ctk.CTkFont(size=18)).pack(side="left", padx=(0, 5))
        self.pass_entry = ctk.CTkEntry(pass_wrapper, placeholder_text="Şifre", show="*", width=210, height=45)
        self.pass_entry.pack(side="left", padx=(0, 5))
        
        self.show_pass_btn = ctk.CTkButton(pass_wrapper, text="👁", width=35, height=45, command=self.toggle_password, fg_color="transparent", border_width=1, hover_color="#2980b9")
        self.show_pass_btn.pack(side="left")

        self.pass_entry.bind("<Return>", lambda e: self.start_login())
        self.user_entry.bind("<Return>", lambda e: self.start_login())
        self.pass_entry.bind("<KeyRelease>", self.check_capslock)

        self.caps_warning = ctk.CTkLabel(self.login_card, text="Caps Lock Açık!", text_color="#f39c12", font=ctk.CTkFont(size=12))

        options_frame = ctk.CTkFrame(self.login_card, fg_color="transparent", width=280)
        options_frame.pack(pady=5, fill="x", padx=60)
        
        self.remember_var = ctk.StringVar(value="on")
        remember_cb = ctk.CTkCheckBox(options_frame, text="Beni Hatırlat", variable=self.remember_var, onvalue="on", offvalue="off", checkbox_width=18, checkbox_height=18, text_color="#bdc3c7")
        remember_cb.pack(side="left")
        
        forgot_lbl = ctk.CTkLabel(options_frame, text="Şifremi Unuttum", text_color="#3498db", cursor="hand2")
        forgot_lbl.pack(side="right")

        self.login_err_label = ctk.CTkLabel(self.login_card, text="", text_color="#e74c3c")
        self.login_err_label.pack(pady=5)

        self.login_btn = ctk.CTkButton(self.login_card, text="GİRİŞ YAP", command=self.start_login, width=280, height=45, font=ctk.CTkFont(weight="bold", size=15), fg_color="#2980b9", hover_color="#3498db")
        self.login_btn.pack(pady=(5, 10))

        # Versiyon Bilgisi
        ctk.CTkLabel(self.current_frame, text="PortLogix V4.0 - Güvenli Giriş Modu Aktif", font=ctk.CTkFont(size=10), text_color="gray").place(relx=0.5, rely=0.98, anchor="s")

        self.after(200, lambda: self.user_entry.focus())

    def check_capslock(self, event):
        try:
            hllDll = ctypes.WinDLL("User32.dll")
            VK_CAPITAL = 0x14
            if hllDll.GetKeyState(VK_CAPITAL) & 1:
                self.caps_warning.place(relx=0.5, rely=0.72, anchor="center")
            else:
                self.caps_warning.place_forget()
        except:
            pass

    def toggle_password(self):
        if self.pass_entry.cget("show") == "*":
            self.pass_entry.configure(show="")
            self.show_pass_btn.configure(text="🙈")
        else:
            self.pass_entry.configure(show="*")
            self.show_pass_btn.configure(text="👁")

    def start_login(self):
        self.login_btn.configure(text="Giriş Yapılıyor...", state="disabled")
        self.user_entry.configure(border_color=["#979da2", "#565b5e"])
        self.pass_entry.configure(border_color=["#979da2", "#565b5e"])
        self.login_err_label.configure(text="")
        
        self.after(800, self.handle_login)

    def handle_login(self):
        self.login_btn.configure(text="GİRİŞ YAP", state="normal")
        username = self.user_entry.get()
        password = self.pass_entry.get()

        role = DataManager.verify_login(username, password)
        if role == "staff":
            self.bg_canvas.after_cancel(self.bg_canvas.animate)
            self.show_staff_frame()
        else:
            self.login_err_label.configure(text="Kullanıcı adı veya şifre hatalı!")
            self.user_entry.configure(border_color="#e74c3c")
            self.pass_entry.configure(border_color="#e74c3c")

    def show_staff_frame(self):
        self.clear_container()
        self.current_frame = StaffFrame(self.container, logout_callback=self.show_login_frame)
        self.current_frame.pack(fill="both", expand=True)

    def show_customer_frame(self):
        self.clear_container()
        if hasattr(self, 'bg_canvas'):
            try: self.bg_canvas.after_cancel(self.bg_canvas.animate)
            except: pass
        self.current_frame = CustomerFrame(self.container, logout_callback=self.show_login_frame)
        self.current_frame.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()
