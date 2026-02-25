from flet import app, Page, Text, TextField, Button, FormField, FormValidator, FormError, FormState, Container, Row, Column, Icon, Tab, Tabs, ListView, ProgressRing, Header, Footer, Padding, BoxShadow, Border, RoundedRectangleBorder, BorderRadius, Alignment, VerticalAlignment

def build_product_card(r: dict, is_cheapest: bool) -> Container:
    # ... entire content of the function ...
    return Container(
        content=card_content,
        bgcolor=BG_CARD,
        border=border,
        border_radius=get_br().only(bottom_left=12, bottom_right=12),
        shadow=shadow,
        clip_behavior=get_clip("HARD_EDGE")
    )

def main(page: Page):
    # ... entire content of the function ...
    page.add(
        header,
        search_bar_container,
        progress_ring,
        ft.Container(content=status_text, padding=get_padding().only(top=12, bottom=4), alignment=ft.Alignment(0, 0)),
        results_list,
        footer
    )

if __name__ == "__main__":
    app(target=main)
