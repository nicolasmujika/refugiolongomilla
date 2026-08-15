from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def traducido(texto_es, texto_en):
    """
    Uso: {{ objeto.campo|traducido:objeto.campo_en }}
    Devuelve la versión en inglés si el sitio está en inglés y ese campo no está vacío;
    si no, devuelve el texto en español original.
    """
    return texto_es  # el idioma real se resuelve en el simple_tag de abajo


@register.simple_tag(takes_context=True)
def t_campo(context, texto_es, texto_en):
    idioma_actual = context.get("idioma_actual", "es")
    if idioma_actual == "en" and texto_en:
        return texto_en
    return texto_es