from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth.models import User
from correspondence.models import Radicate, City, UserProfileInfo, Person, Record
from pinax.eventlog.models import log, Log
from django.urls import reverse
from crispy_forms.layout import Field, ButtonHolder, Button


class CustomFileInput(Field):
    template = 'custom_fileinput.html'


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password')


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserProfileInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfileInfo
        exclude = ('user',)


class RadicateForm(forms.ModelForm):
    class Meta:
        model = Radicate
        fields = ['use_parent_address', 'subject', 'annexes', 'observation', 'type', 'reception_mode', 'document_file',
                  'office', 'doctype']
        labels = {'use_parent_address': '¿Usar la dirección de la organización?', 'subject': 'Asunto',
                  'person': 'Remitente/Destinatario',
                  'annexes': 'Anexos', 'type': 'Tipo', 'reception_mode': 'Medio de recepción',
                  'document_file': 'Documento', 'observation': 'Observaciones', 'office': 'Dependencia',
                  'doctype': 'Tipo de documento'}
        widgets = {
            'type': forms.Select(attrs={'class': 'selectpicker'}),
            'reception_mode': forms.Select(attrs={'class': 'selectpicker'}),
            'subject': forms.TextInput(),
            'annexes': forms.TextInput(),
            'office': forms.Select(attrs={'class': 'selectpicker'}),
            'doctype': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7',
                                           'title': 'Seleccione..'})
        }

    def __init__(self, *args, **kwargs):
        super(RadicateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'use_parent_address',
            Row(
                Column('type', css_class='form-group col-md-6 mb-0'),
                Column('reception_mode', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'subject',
            'observation',
            'annexes',
            'office',
            'doctype',
            CustomFileInput('document_file'),
            Submit('submit', 'Radicar')
        )


class SearchForm(forms.Form):
    item = forms.CharField(label='Palabra clave', help_text='Datos a buscar')


class SearchContentForm(forms.Form):
    term = forms.CharField(label='Búsqueda por términos clave', help_text='Introduzca el termino a buscar')


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person

        fields = ['document_type', 'document_number', 'name', 'email', 'city', 'address', 'parent']
        labels = {'document_type': 'Tipo de documento',
                  'document_number': 'Número de documento',
                  'name': 'Nombres', 'email': 'Correo electrónico',
                  'city': 'Ciudad / Municipio', 'address': 'Dirección',
                  'parent': 'Entidad'}

        widgets = {
            'document_type': forms.Select(attrs={'class': 'selectpicker'}),
            'city': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'parent': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
        }

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields['parent'].queryset = Person.objects.filter(document_type='NIT')
        self.helper.layout = Layout(
            Row(
                Column('document_type', css_class='form-group col-md-6 mb-0'),
                Column('document_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('address', css_class='form-group col-md-6 mb-0'),
                Column('city', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'parent',
            Submit('submit', 'Guardar')
        )


class ChangeCurrentUserForm(forms.ModelForm):
    class Meta:
        model = Radicate
        fields = ['current_user']
        labels = {'current_user': 'Usuario'}
        widgets = {
            'current_user': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true'})
        }

    def save(self, commit=True):
        radicate = super(ChangeCurrentUserForm, self).save(commit=False)
        log(
            user=radicate.current_user.user,
            action="RADICATE_CHANGE_USER",
            obj=radicate,
            extra=dict(number=radicate.number, message="Se ha re-asignado el usuario actual")
        )

        if commit:
            radicate.save()
        return radicate

class RecordForm(forms.ModelForm):
    class Meta:
        model = Record

        fields = ['retention', 'responsable', 'process_type', 'phase', 'final_disposition', 'security_level', 'is_tvd', 
            'name', 'subject', 'source', 'init_process_date', 'init_date', 'final_date']
        labels = {'retention': 'Tipificación',
                  'responsable': 'Usuario Responsable del Proceso',
                  'process_type': 'Proceso', 'phase': 'Fase',
                  'final_disposition': 'Disposición final', 'security_level': 'Nivel de seguridad',
                  'is_tvd': '¿Es Tabla de Valoración Documental?', 'name': 'Nombre', 'subject': 'Asunto', 'source': 'Fuente', 'init_process_date': 'Fecha inicial del proceso',
                  'init_date': 'Fecha inicial', 'final_date': 'Fecha final'}

        widgets = {
            'retention': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'responsable': forms.Select(attrs={'class': 'selectpicker', 'data-live-search': 'true', 'data-size': '7'}),
            'init_process_date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'init_date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'final_date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            )
        }

    # def save(self, commit=True):
    #     record = super(RecordForm, self).save(commit=False)
    #     # log(
    #     #     user='',
    #     #     action="RECORD_SAVE",
    #     #     obj=record,
    #     #     extra=dict(number=radicate.number, message="Se ha guardado el expediente")
    #     # )

    #     if commit:
    #         record.save()
    #     return record

    def __init__(self, *args, **kwargs):
        super(RecordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        cancel_url = reverse('correspondence:list_records')
        self.helper.layout = Layout(
            Row(
                Column('is_tvd', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('name', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('retention', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('subject', css_class='form-group col-md-6 mb-0'),
                Column('source', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('process_type', css_class='form-group col-md-6 mb-0'),
                Column('responsable', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('init_process_date', css_class='form-group col-md-4 mb-0'),
                Column('init_date', css_class='form-group col-md-4 mb-0'),
                Column('final_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('phase', css_class='form-group col-md-4 mb-0'),
                Column('final_disposition', css_class='form-group col-md-4 mb-0'),
                Column('security_level', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            ButtonHolder(
                Submit('submit', 'Guardar', css_class='btn btn-success'),
                Button('cancel', 'Volver', onclick='window.location.href="{}"'.format(cancel_url), css_class='btn btn-primary')
            )
        )
