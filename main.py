"""
ParçaPusula - Mobile PWA Frontend (Vercel API Entegreli)
UI/UX Theme: Dark Industrial Elegance - 58 Sanayi Edisyonu
======================================================
"""
import asyncio
import httpx
import flet as ft

# ─────────────────────────── Tema ve Renk Paleti ────────────────────────────
BG_DARK      = "#121212"   # Derin antrasit gri (Ana Zemin)
BG_CARD      = "#1E1E1E"   # Bir ton açık antrasit (Kart Zemini)
AMBER        = "#FFB300"   # Kehribar Sarısı/Turuncusu (Aksan, Butonlar, Fiyat)
TEXT_WHITE   = "#E0E0E0"   # Kırık Beyaz (Okunabilirlik için)
TEXT_GREY    = "#9E9E9E"   # Gri (Satıcı, Alt Bilgiler)
GREEN_NEON   = "#00C853"   # Neon Yeşil (En Ucuz Vurgusu)
RED_ERR      = "#FF5252"
YELLOW_WARN  = "#FFC107"

# API_URL = "/api/search" # Sunucu tarafında doğrudan ScraperEngine kullanılacak
from scraper import ScraperEngine
from flet_resolver import (
    get_icon, get_fw, get_align, get_cross, get_fit, 
    get_overflow, get_scroll, get_clip, get_color,
    get_padding, get_margin, get_br
)

# ─────────────────────────── UI Bileşenleri (Components) ────────────────────
def build_product_card(r: dict, is_cheapest: bool) -> ft.Container:
    """Dark Industrial Elegance konseptine uygun e-ticaret stili ürün kartı."""
    
    # Kart temeli ve gölgesi
    shadow = ft.BoxShadow(
        spread_radius=1,
        blur_radius=15,
        color=f"{GREEN_NEON}33" if is_cheapest else "#00000033", 
        offset=ft.Offset(0, 4),
    )
    
    border = ft.Border.all(1, GREEN_NEON if is_cheapest else "#333333")

    # En Ucuz Rozeti
    badge = ft.Container(
        content=ft.Row([
            ft.Icon(get_icon("NEW_RELEASES_OUTLINED"), color="#fff", size=14),
            ft.Text("EN İYİ FİYAT", size=11, color="#fff", weight=get_fw("W_900"))
        ], spacing=4, alignment=get_align("CENTER")),
        bgcolor=GREEN_NEON,
        border_radius=get_br().only(top_left=12, bottom_right=12),
        padding=get_padding().symmetric(horizontal=10, vertical=4),
        visible=is_cheapest
    )

    success = r.get("success", False)
    # Define graceful disabled states
    graceful_errors = [
        "Bu sitede ürün bulunamadı", 
        "Site Koruma Altında", 
        "Site Koruma Altında (403)", 
        "Fiyat Alınamadı", 
        "Zaman aşımı — site yanıt vermedi.",
        "Site Koruma Altında (Bot Koruması)"
    ]
    is_not_found = (not success) and (r.get("status") in graceful_errors)
    
    # Başlık Alanı
    title_text = ft.Text(
        r.get("part_name", "") if success else r.get("status", "Erişim Hatası"),
        size=15,
        color=TEXT_WHITE if success else (TEXT_GREY if is_not_found else RED_ERR),
        weight=get_fw("W_500"),
        max_lines=2,
        overflow=get_overflow("ELLIPSIS"),
    )

    # Fiyat Alanı
    price_val = r.get("price_str", "—") if success else ("Stokta Yok" if is_not_found else "—")
    price_text = ft.Text(
        price_val,
        size=28 if success else 20,
        color=AMBER if success else TEXT_GREY,
        weight=get_fw("BOLD"),
    )

    # Satıcı (Site) ve Favicon
    domain_map = {
        "OnlineYedekParca": "onlineyedekparca.com",
        "AlloYedekParca": "aloparca.com",
        "ParcaDeposu": "otoparcadeposu.com",
        "n11": "n11.com",
        "Hepsiburada": "hepsiburada.com",
        "Sahibinden": "sahibinden.com"
    }
    site_name = r.get("site", "Bilinmeyen")
    domain = domain_map.get(site_name, "google.com")
    favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

    seller_text = ft.Text(
        site_name if not is_not_found else f"{site_name} (Sonuç Yok)",
        size=13,
        color=TEXT_GREY,
    )
    
    engine_val = r.get("engine", "Stealth")
    is_scraperapi = "ScraperAPI" in engine_val
    engine_badge = ft.Container(
        content=ft.Text(engine_val, size=10, weight=get_fw("BOLD"), color=BG_DARK),
        bgcolor=get_color("RED_400") if is_scraperapi else get_color("GREEN_400"),
        border_radius=4,
        padding=get_padding().symmetric(horizontal=4, vertical=2)
    )

    seller_row = ft.Row([
        ft.Image(src=favicon_url, width=16, height=16, fit=get_fit("CONTAIN")),
        seller_text,
        engine_badge if success else ft.Container()
    ], spacing=6, alignment=get_align("END"), vertical_alignment=get_cross("CENTER"))

    buy_button = ft.FilledButton(
        content=ft.Row([
            ft.Text("Siteye Git" if success else "Stokta Yok", size=15, weight=get_fw("BOLD")),
            ft.Icon(get_icon("ARROW_OUTWARD") if success else get_icon("NOT_INTERESTED"), size=18)
        ], alignment=get_align("CENTER"), spacing=6),
        url=r.get("affiliate_url", "") if success else None,
        style=ft.ButtonStyle(
            color=BG_DARK if success else TEXT_GREY,
            bgcolor=AMBER if success else BG_DARK,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=get_padding().symmetric(vertical=16)
        ),
        disabled=not success
    )
    
    # WhatsApp Paylaşım Entegrasyonu
    import urllib.parse
    part = r.get('part_name', 'Ürün')
    link = r.get('affiliate_url', r.get('url', ''))
    msg = f"Ustam bak, en ucuz {part} {price_val} ile ParçaPusula'da bulundu! Link: {link}"
    wa_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
    
    wa_button = ft.IconButton(
        icon=get_icon("SHARE"),
        icon_color=get_color("GREEN_400") if success else TEXT_GREY,
        tooltip="WhatsApp ile Paylaş",
        url=wa_url if success else None,
        disabled=not success,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=12)
    )
    
    # Buton konteyneri (Tam genişlik için Row)
    button_row = ft.Row([buy_button, wa_button] if success else [buy_button], expand=True)
    buy_button.expand = True

    card_content = ft.Column(
        [
            ft.Row([badge], alignment=get_align("START")) if is_cheapest else ft.Container(height=0),
            ft.Container(
                content=ft.Column(
                    [
                        title_text,
                        ft.Container(height=8),
                        ft.Row(
                            [
                                ft.Column([price_text, seller_row], spacing=4),
                            ],
                            alignment=get_align("SPACE_BETWEEN"),
                            vertical_alignment=get_cross("END")
                        ),
                        ft.Container(height=16),
                        button_row
                    ],
                    spacing=0
                ),
                padding=get_padding().only(left=16, right=16, bottom=16, top=8 if is_cheapest else 16)
            )
        ],
        spacing=0
    )

    return ft.Container(
        content=card_content,
        bgcolor=BG_CARD,
        border=border,
        border_radius=12,
        margin=get_margin().only(bottom=16),
        shadow=shadow,
        clip_behavior=get_clip("HARD_EDGE")
    )


# ─────────────────────────── Ana Uygulama Gidişatı ───────────────────────
def main(page: ft.Page):
    # ── PWA & Mobil Sayfa Ayarları ──
    page.title = "ParçaPusula | 58"
    page.bgcolor = BG_DARK
    page.padding = 0
    page.window_width = 400
    page.window_height = 800
    page.theme = ft.Theme(font_family="Roboto")
    page.scroll = get_scroll("HIDDEN") 

    searching = False
    search_type = "parca"

    # ── Arama Çubuğu ve Toggle ──
    search_field = ft.TextField(
        hint_text="Parça adı veya kodu...",
        hint_style=ft.TextStyle(color=TEXT_GREY, size=14),
        border_color="#333333",
        focused_border_color=AMBER,
        color=TEXT_WHITE,
        bgcolor=BG_DARK,
        cursor_color=AMBER,
        text_size=15,
        border_radius=8,
        content_padding=get_padding().symmetric(horizontal=12, vertical=12),
        expand=True,
        on_submit=lambda e: asyncio.ensure_future(do_search()),
        prefix_icon=get_icon("SEARCH")
    )

    def toggle_search_type(e):
        nonlocal search_type
        if e.control.selected_index == 0:
            search_type = "parca"
            search_field.hint_text = "Parça adı veya kodu..."
            search_field.prefix_icon = get_icon("SEARCH")
        else:
            search_type = "sasi"
            search_field.hint_text = "17 Haneli Şasi No Giriniz..."
            search_field.prefix_icon = get_icon("DIRECTIONS_CAR")
        page.update()

    search_toggle = ft.Tabs(
        selected_index=0,
        on_change=toggle_search_type,
        tabs=[
            ft.Tab(text="Parça Ara"),
            ft.Tab(text="Şasi No"),
        ],
        expand=True,
    )

    # ── Yükleme ve Durum Göstergesi ──
    progress_ring = ft.Container(
        content=ft.ProgressRing(color=AMBER, stroke_width=3, width=24, height=24),
        alignment=ft.Alignment(0, 0),
        padding=20,
        visible=False
    )
    status_text = ft.Text(
        "Aramaya başlamak için bilgi girin.", 
        size=14, 
        color=TEXT_GREY, 
        text_align=get_align("CENTER")
    )
    
    results_list = ft.ListView(
        spacing=0,
        padding=get_padding().symmetric(horizontal=16, vertical=8),
        expand=True,
        auto_scroll=False
    )

    async def do_search():
        nonlocal searching
        if searching: return

        query = search_field.value.strip()
        if not query:
            status_text.value = "Lütfen bir arama terimi girin."
            status_text.color = YELLOW_WARN
            page.update()
            return
            
        if search_type == "sasi" and len(query) != 17:
             status_text.value = "Şasi numarası tam 17 haneli olmalıdır."
             status_text.color = YELLOW_WARN
             page.update()
             return

        searching = True
        progress_ring.visible = True
        status_text.value = f"'{query}' aranıyor..."
        status_text.color = TEXT_WHITE
        results_list.controls.clear()
        page.update()

        try:
            # VERCEL FIX: HTTPX ile localhost'a istek atmak yerine doğrudan ScraperEngine'i çağırıyoruz.
            # Bu hem performansı artırır hem de Vercel'deki yönlendirme/bağlantı hatalarını önler.
            engine = ScraperEngine()
            results_raw = await engine.search_all(query)
            
            # Sonuçları API formatına dönüştürüyoruz (mevcut UI kodunun bozulmaması için)
            results = [
                {
                    "site": r.site_name,
                    "success": r.success,
                    "part_name": r.part_name,
                    "price_str": r.price_str,
                    "price_numeric": r.price_numeric,
                    "url": r.url,
                    "affiliate_url": r.affiliate_url,
                    "engine": getattr(r, "engine", "Stealth"),
                    "status": r.error_msg if not r.success else "OK"
                }
                for r in results_raw
            ]
        except Exception as exc:
            import traceback
            traceback.print_exc()
            status_text.value = f"Arama sırasında hata oluştu: {str(exc)[:50]}"
            status_text.color = RED_ERR
            results = []
        finally:
            searching = False
            progress_ring.visible = False

        if not results:
            if not status_text.color == RED_ERR:
                status_text.value = "Bu parçaya ait sonuç bulunamadı."
            page.update()
            return

        successful = [r for r in results if r.get("success") and r.get("price_numeric") is not None]
        cheapest_price = min((r.get("price_numeric") for r in successful), default=None)

        # Kartları hazırlayıp listeye ekle
        for r in results:
            is_cheapest = (
                r.get("success")
                and r.get("price_numeric") is not None
                and r.get("price_numeric") == cheapest_price
            )
            results_list.controls.append(build_product_card(r, is_cheapest))

        success_count = len(successful)
        status_text.value = f"{success_count} sonuç bulundu." if success_count > 0 else "Gerçek zamanlı sonuç alınamadı."
        status_text.color = GREEN_NEON if success_count > 0 else RED_ERR
        page.update()

    # ── Header Alanı (Markalama) ──
    header = ft.Container(
        content=ft.Row([
            ft.Icon(get_icon("PRECISION_MANUFACTURING"), color=AMBER, size=32), # Sanayi İkonu
            ft.Column([
                ft.Text("ParçaPusula | Sivas Sanayi", size=22, color=TEXT_WHITE, weight=get_fw("W_900")),
                ft.Text("Sivas Sanayi Özel Edisyonu", size=12, color=AMBER, weight=get_fw("W_500"), italic=True),
            ], spacing=2)
        ], alignment=get_align("START"), vertical_alignment=get_cross("CENTER")),
        padding=get_padding().only(left=16, right=16, top=20, bottom=10)
    )

    # ── Yapışık (Sticky) Arama Arayüzü ──
    search_bar_container = ft.Container(
        content=ft.Column([
            ft.Row([search_toggle]),
            ft.Row([
                search_field,
                ft.IconButton(
                    icon=get_icon("SEARCH"),
                    icon_color=BG_DARK,
                    bgcolor=AMBER,
                    icon_size=24,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=12),
                    on_click=lambda e: asyncio.ensure_future(do_search())
                )
            ]),
        ], spacing=12),
        bgcolor=BG_CARD,
        padding=get_padding().all(16),
        border_radius=get_br().only(bottom_left=16, bottom_right=16),
        shadow=ft.BoxShadow(blur_radius=10, color="#00000040", offset=ft.Offset(0, 4))
    )

    # ── İmza (Footer) ──
    footer = ft.Container(
        content=ft.Column([
            ft.Text("Developed by Onurcan KAYA | Mapping Engineer", size=11, italic=True, color=get_color("GREY_500"), text_align=get_align("CENTER"))
        ], horizontal_alignment=get_cross("CENTER"), spacing=4),
        alignment=ft.Alignment(0, 0),
        padding=get_padding().only(top=20, bottom=30)
    )

    page.add(
        header,
        search_bar_container,
        progress_ring,
        ft.Container(content=status_text, padding=get_padding().only(top=12, bottom=4), alignment=ft.Alignment(0, 0)),
        results_list,
        footer
    )

if __name__ == "__main__":
    ft.app(target=main)

