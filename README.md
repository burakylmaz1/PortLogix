## PortLogix V4 - Liman Otomasyon Sistemi

PortLogix, liman işletmelerindeki mal kabul, gümrükleme, maliyet hesaplama ve sevkiyat süreçlerini dijitalleştirmek için geliştirilmiş, rol tabanlı bir yönetim sistemidir. Sistem, hem saha görevlilerinin operasyonel işlemlerini yönetebileceği hem de müşterilerin kargo durumlarını anlık takip edebileceği entegre bir yapı sunar.

---

### Temel Özellikler

* **Rol Tabanlı Erişim Kontrolü (RBAC)**: Görevli ve müşteri rolleri için özelleştirilmiş farklı giriş panelleri ve yetki tanımları.
* **Gelişmiş Takip Sistemi**: Plaka veya otomatik oluşturulan takip numarası (PLX formatı) ile kargo sorgulama.
* **Maliyet Hesaplama Motoru**: Gümrük maliyeti, KDV ve elleçleme giderlerini içeren Landed Cost (Maliyet) hesaplama.
* **Dinamik Durum Yönetimi**: Kargonun limana girişinden çıkışına kadar olan tüm süreçlerin (Giriş Yaptı, Gümrükte, Elleçleniyor, Çıkışa Hazır) anlık takibi.
* **PDF Makbuz Oluşturma**: Müşteriler için detaylı maliyet dökümünü içeren dijital makbuz üretimi.
* **Veri Analitiği ve Raporlama**: Görevli paneli üzerinden görsel istatistikler (Pie Chart) ve Excel formatında toplu veri dışa aktarımı.
* **Akıllı Arşivleme**: İşlemi tamamlanan kayıtların ana sistemden arşive taşınması ve ihtiyaç anında geri yüklenmesi.
* **Otomatik QR Kod Üretimi**: Her kargo için plaka ve takip numarası bilgilerini içeren gömülü QR kod desteği.

---

### Teknik Detaylar

* **Programlama Dili**: Python 3.13.
* **Arayüz (UI)**: CustomTkinter kütüphanesi ile modern ve karanlık mod destekli tasarım.
* **Veritabanı**: SQLite3 entegrasyonu ile yerel veri depolama.
* **Veri Analizi**: Pandas kütüphanesi ile veritabanı sorgulama ve raporlama işlemleri.
* **Grafik**: Matplotlib ile operasyonel istatistiklerin görselleştirilmesi.

---

### Kurulum Talimatları

1. **Gereksinimlerin Yüklenmesi**:
Terminal üzerinden gerekli kütüphaneleri yüklemek için aşağıdaki komutu çalıştırın:
```bash
pip install -r requirements.txt

```


2. **Veritabanı Başlatma**:
Sistemi ilk kez çalıştırmadan önce veritabanı şemasını oluşturmak için:
```bash
python database.py

```


*Not: Varsayılan admin girişi için kullanıcı adı: admin, şifre: admin123 olarak belirlenmiştir.*
3. **Uygulamayı Çalıştırma**:
Ana uygulama arayüzünü başlatmak için:
```bash
python main.py

```



---

### Dosya Yapısı

* **main.py**: Uygulamanın giriş noktası ve login yönetimini sağlayan ana dosya.
* **database.py**: SQLite veritabanı tablolarının oluşturulması ve bağlantı ayarları.
* **logic.py**: Maliyet hesaplama, takip no üretimi, veri işleme ve loglama mantığı.
* **ui_staff.py**: Liman görevlileri için geliştirilen yönetim paneli arayüzü.
* **ui_customer.py**: Müşteriler için geliştirilen kargo sorgulama ve takip arayüzü.
* **requirements.txt**: Projenin çalışması için gerekli olan bağımlılıklar listesi.
* **log.txt**: Sistemde yapılan ekleme, güncelleme ve silme işlemlerinin kayıt defteri.
