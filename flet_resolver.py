import flet as ft

def get_ft_attr(module_name: str, attr_name: str, default=None):
    """Flet'in farklı sürümlerindeki isimlendirme farklarını (Icons vs icons) çözer."""
    # 1. Doğrudan ft üzerinde ara (Bazı enums/consts taşınmış olabilir)
    if hasattr(ft, attr_name):
        return getattr(ft, attr_name)
    if hasattr(ft, attr_name.lower()):
        return getattr(ft, attr_name.lower())
    if hasattr(ft, attr_name.upper()):
        return getattr(ft, attr_name.upper())

    # 2. Modül (Sub-module) içinde ara
    module = getattr(ft, module_name, None)
    if module:
        if hasattr(module, attr_name):
            return getattr(module, attr_name)
        if hasattr(module, attr_name.lower()):
            return getattr(module, attr_name.lower())
        if hasattr(module, attr_name.upper()):
            return getattr(module, attr_name.upper())
            
    return default

# Kısayollar
def get_icon(name: str): return get_ft_attr("icons", name, ft.icons.QUESTION_MARK if hasattr(ft, "icons") else None)
def get_fw(name: str): return get_ft_attr("font_weight", name)
def get_align(name: str): return get_ft_attr("main_axis_alignment", name) or get_ft_attr("text_align", name)
def get_cross(name: str): return get_ft_attr("cross_axis_alignment", name)
def get_fit(name: str): return get_ft_attr("box_fit", name)
def get_overflow(name: str): return get_ft_attr("text_overflow", name)
def get_scroll(name: str): return get_ft_attr("scroll_mode", name)
def get_clip(name: str): return get_ft_attr("clip_behavior", name)
def get_color(name: str): return get_ft_attr("colors", name)
def get_padding(): return getattr(ft, "padding", getattr(ft, "Padding", None))
def get_margin(): return getattr(ft, "margin", getattr(ft, "Margin", None))
def get_br(): return getattr(ft, "border_radius", getattr(ft, "BorderRadius", None))
