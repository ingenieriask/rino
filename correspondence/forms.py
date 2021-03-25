from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth.models import User
from correspondence.models import Radicate, City, UserProfileInfo, Person
from pinax.eventlog.models import log, Log
from crispy_forms.layout import Field


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
