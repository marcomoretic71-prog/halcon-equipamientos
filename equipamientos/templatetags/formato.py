from django import template
register = template.Library()

@register.filter
def ars(value):
    """
    Formatea 21521.5 -> $ 21.521,50
    Si es 0 o vacio -> devuelve "" para que no moleste
    """
    try:
        v = float(value or 0)
        if v == 0:
            return ""
        # Formateo US y luego intercambio
        s = f"{v:,.2f}"  # 21,521.50
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")  # 21.521,50
        return f"$ {s}"
    except:
        return ""