from django import forms

from .models import Casa, Reserva, Servicio

CODIGOS_PAIS = [
    ("+56", "+56"),
    ("+54", "+54"),
    ("+51", "+51"),
    ("+591", "+591"),
    ("+57", "+57"),
    ("+52", "+52"),
    ("+1", "+1"),
    ("+34", "+34"),
    ("+55", "+55"),
    ("+49", "+49"),
    ("+33", "+33"),
    ("+44", "+44"),
]


class ReservaForm(forms.ModelForm):
    codigo_pais = forms.ChoiceField(choices=CODIGOS_PAIS, initial="+56", label="Código de país")

    servicios = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.filter(activo=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Servicios extra",
    )

    class Meta:
        model = Reserva
        fields = ["casa", "fecha_llegada", "fecha_salida", "huespedes", "nombre", "email", "codigo_pais", "contacto", "mensaje", "servicios"]
        widgets = {
            "fecha_llegada": forms.DateInput(attrs={"type": "date"}),
            "fecha_salida": forms.DateInput(attrs={"type": "date"}),
            "contacto": forms.TextInput(attrs={"placeholder": "9 1234 5678"}),
            "mensaje": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, idioma="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["casa"].queryset = Casa.objects.filter(activa=True)

        # Obligatorios
        self.fields["casa"].required = True
        self.fields["fecha_llegada"].required = True
        self.fields["fecha_salida"].required = True
        self.fields["huespedes"].required = True
        self.fields["nombre"].required = True
        self.fields["email"].required = True
        self.fields["codigo_pais"].required = True
        self.fields["contacto"].required = True

        # Opcionales
        self.fields["mensaje"].required = False
        self.fields["servicios"].required = False

        if idioma == "en":
            self.fields["casa"].label_from_instance = lambda obj: obj.nombre_en or obj.nombre
            self.fields["servicios"].label_from_instance = lambda obj: obj.nombre_en or obj.nombre

    def clean(self):
        cleaned_data = super().clean()
        casa = cleaned_data.get("casa")
        llegada = cleaned_data.get("fecha_llegada")
        salida = cleaned_data.get("fecha_salida")

        if not (casa and llegada and salida):
            return cleaned_data

        if salida <= llegada:
            self.add_error("fecha_salida", "La fecha de salida debe ser posterior a la de llegada.")
            return cleaned_data

        conflictos = Reserva.objects.filter(
            casa=casa,
            estado__in=["pendiente", "confirmada"],
        ).exclude(
            fecha_llegada__isnull=True
        ).exclude(
            fecha_salida__isnull=True
        ).filter(
            fecha_llegada__lt=salida,
            fecha_salida__gt=llegada,
        )

        if self.instance and self.instance.pk:
            conflictos = conflictos.exclude(pk=self.instance.pk)

        if conflictos.exists():
            self.add_error(
                "fecha_llegada",
                "Esas fechas ya están reservadas para esta casa. Elige otras fechas o consulta disponibilidad."
            )

        return cleaned_data