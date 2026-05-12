# Proje: PortLogix V2 - Çok Rollü Liman Otomasyon Sistemi

## 1. Proje Amacı
Liman işletmelerinde, müşteriler ve görevliler için özelleştirilmiş iki farklı arayüz üzerinden lojistik, gümrük ve maliyet süreçlerini basitleştirilmiş bir yapıda yönetmek.

## 2. Teknik Gereksinimler
- **Dil:** Python 3.x
- **Kütüphaneler:** `customtkinter` (UI), `sqlite3` (DB), `pandas` (Veri İşleme)
- **Mimari:** Role-Based Access Control (Rol Bazlı Erişim Kontrolü)

## 3. Kullanıcı Rolleri ve Yetki Tanımları

### A. Liman Görevlisi (Admin/Operatör)
- **Erişim:** Tam Yetki.
- **Ana Dashboard:** Tüm giriş yapan araçların/malların listesi.
- **Mal Kabul:** Yeni mal girişi yapma ve maliyetleri sisteme girme.
- **Durum Yönetimi:** Malın sürecini (Giriş Yaptı, Gümrükte, Elleçleniyor, Çıkışa Hazır) güncelleme.
- **Arşivleme:** İşlemi biten kayıtları ana ekrandan kaldırma.

### B. Müşteri (Sorgu Ekranı)
- **Erişim:** Kısıtlı (Sadece kendi malını görme).
- **Takip Ekranı:** Plaka veya takip numarası ile sorgulama.
- **Görsel Takip:** Malın limandaki aşamasını gösteren ilerleme çubuğu.
- **Maliyet Detayı:** Ödenmesi gereken toplam ücretin (Gümrük, KDV, Elleçleme) kalem bazlı kırılımı.

## 4. Veri Tabanı Mimarisi
`shipments` tablosuna eklenecek ek alanlar:
- `current_status` (String: Beklemede / İşlemde / Tamamlandı)
- `customer_id` (String/ID: Müşterinin takip edebilmesi için)
- `last_update` (Timestamp: Durumun en son ne zaman güncellendiği)

## 5. UI/UX Tasarım Detayları
- **Login Ekranı:** Kullanıcı türüne göre (Görevli/Müşteri) farklı Dashboard'lara yönlendirme yapan giriş sistemi.
- **Görevli Tablosu:** Kritik durumdaki (örn: 3 günden fazla bekleyen) malların satırlarının belirginleştirilmesi.
- **Müşteri Kartı:** Karmaşık tablolardan uzak, mobil uyumlu görünüme sahip büyük bilgi kartları.

## 6. Antigravity İçin Özel Talimatlar
1. **Dinamik UI:** `main.py` içerisinde kullanıcı giriş yaptıktan sonra `frame_manager` kullanarak sadece o role ait `Frame` yapısını yükle.
2. **Hesaplama Motoru:** Maliyet hesaplama fonksiyonu (Landed Cost) `logic.py` içerisinde merkezi bir sınıfta tutulmalı; hem görevli hem müşteri aynı kaynaktan veri almalı.
3. **Validasyon:** Müşteri sorgu ekranında, olmayan bir takip numarası girildiğinde kullanıcıya dostça bir hata mesajı göster.
4. **Veri Güvenliği:** Müşteri arayüzünde diğer müşterilere ait bilgilerin (plaka, fiyat vb.) listelenmediğinden emin ol.