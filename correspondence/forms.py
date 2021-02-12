from django import forms
from django.contrib.auth.models import User
from correspondence.models import Radicate,City,UserProfileInfo,Person


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta():
        model = User
        fields = ('username','first_name','last_name','email','password')


class UserProfileInfoForm(forms.ModelForm):

    class Meta():
        model = UserProfileInfo
        exclude = ('user',)


class RadicateForm(forms.ModelForm):

    address = forms.ChoiceField(label='Dirección',help_text='Dirección',widget=forms.Select(attrs={'class':'selectpicker'}))

    class Meta:
        model = Radicate
        fields = ['subject','type','reception_mode','document_file']
        labels = {'subject':'Asunto','person':'Remitente/Destinatario','type':'Tipo','reception_mode':'Medio de recepción','document_file':'Documento'}
        widgets = {
                'type' :forms.Select(attrs={'class': 'selectpicker'}),
                'reception_mode' :forms.Select(attrs={'class': 'selectpicker'}),
                'subject': forms.TextInput()
        }


class SearchForm(forms.Form):
    item = forms.CharField(label='Palabra clave',help_text='Datos a buscar')


class SearchContentForm(forms.Form):
    term = forms.CharField(label='Búsqueda por terminos clave',help_text='Introduzca el termino a buscar')


class PersonForm(forms.ModelForm):

    class Meta:
        model = Person

        fields = ['document_type','document_number','name','email','city','address','parent']
        labels = { 'document_type':'Tipo de documento',
        'document_number':'Número de documento',
        'name':'Nombres','email':'Correo electrónico',
        'city':'Ciudad','address':'Dirección',
        'parent':'Entidad'}

        widgets = {
            'document_type':forms.Select(attrs={'class': 'selectpicker'}),
            'city':forms.Select(attrs={'class': 'selectpicker','data-live-search':'true','data-size':'7'})
        }


    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = Person.objects.filter(document_type='NIT')


class ChangeCurrentUserForm(forms.ModelForm):
    class Meta:
        model = Radicate
        fields = ['current_user']
        labels = {'current_user':'Usuario actual'}
        widgets = {
            'current_user':forms.Select(attrs={'class':'selectpicker','data-live-search':'true'})
         }
