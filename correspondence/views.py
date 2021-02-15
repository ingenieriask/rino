from django.shortcuts import render
from correspondence.forms import RadicateForm , SearchForm, UserForm,  UserProfileInfoForm, PersonForm, SearchContentForm, ChangeCurrentUserForm
from datetime import datetime
from django.utils.timezone import get_current_timezone
from django.conf import settings
from correspondence.models import Radicate, Person
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login,logout
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.postgres.search import SearchVector, TrigramSimilarity


import requests
import json
import os
from docx import Document

from requests.auth import HTTPBasicAuth


# Index view

def index(request):
    return render(request,'correspondence/index.html',{})


# LOGIN / LOG OUT  views
def user_login(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username,password=password)

        if user:
            if user.is_active:
                login(request,user)
                return HttpResponseRedirect(reverse('correspondence:list_radicate'))
            else:
                return HttpResponse("Cuenta inactiva")
        else:
            print("Login failed..")
            print("username: {} password: {} ".format(username,password))
            message = "Ingreso inválido"
            return render(request,'correspondence/login.html',{'message':message})

    else:
        return render(request,'correspondence/login.html',{})



def register(request):

    registered = False
    message = None

    if request.method == 'POST':

        user_form = UserForm(data=request.POST)
        user_profile_form = UserProfileInfoForm(data=request.POST)

        if user_form.is_valid() and user_profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = user_profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

                profile.save()
                registered = True

            message = "El usuario ha sido creado con éxito"
            user_form = UserForm()
        else:
            print(user_form.errors,user_profile_form.errors)
    else:
        user_form = UserForm()
        user_profile_form = UserProfileInfoForm()

    return render(request,'correspondence/registration.html',context={'user_form':user_form,'user_profile_form':user_profile_form,'message':message})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('correspondence:index'))


# Search by content

@login_required
def search_by_content(request):
    term = ''
    results = None
    response = None
    error = None
    if request.method == 'POST':
        form = SearchContentForm(data=request.POST)
        term = request.POST.get("term")
        if term != None:
            headers = {'Content-Type': 'application/json'}
            try:
                response = requests.post(
                    settings.ECM_SEARCH_URL,
                    json = { 'query':{'query':term}},
                    auth = HTTPBasicAuth(settings.ECM_USER, settings.ECM_PASSWORD),
                    headers=headers
                )
                results=response.json()['list']['entries']
                print(results)
            except:
                error = "Ha occurrido un error al realizar la búsqueda, por favor intente más tarde"
    else:
        form = SearchContentForm()

    return render(request,'correspondence/content_search.html',context={'term':term,'results':results,'error':error,'form':form})

# Search by names

@login_required
def search_names(request):

    if request.method == 'POST':
        form=SearchForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['item']
            qs = Person.objects.annotate(search=SearchVector('document_number','email','name','address','parent__name'),).filter(search=item)
            if not qs.count():
                 person_form = PersonForm(initial={'name':request.POST.get("item")})
            else:
                 person_form = PersonForm()
    else:
        form = SearchForm()
        qs = None
        person_form = None

    return render(request,'correspondence/search.html',context={'form':form,'list':qs,'person_form':person_form})


# autocomplete

def autocomplete(request):
    if 'term' in request.GET:
        qs = Person.objects.filter(name__icontains=request.GET.get(('term')))
        names = list()
        for person in qs:
            names.append(person.name)
        return JsonResponse(names, safe=False)


# Radicate Views

@login_required
def create_radicate(request,person):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    person = get_object_or_404(Person,id=person)

    if request.method == 'POST':
        form = RadicateForm(request.POST,request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            form.document_file = request.FILES['document_file']
            now = datetime.now()
            instance.number = now.strftime("%Y%m%d%H%M%S")
            instance.creator = request.user
            instance.current_user = request.user
            instance.person = person
            radicate = form.save()


            print(os.path.join(BASE_DIR,instance.document_file.path))

            url = settings.ECM_UPLOAD_URL
            auth = (settings.ECM_USER, settings.ECM_PASSWORD)
            files = {"filedata": open(os.path.join(BASE_DIR,radicate.document_file.path), "rb")}
            data = {"siteid": "swsdp", "containerid": "documentLibrary"}

            try:
                r = requests.post(url, files=files, data=data, auth=auth)
                print(r.status_code)
                json_response =(json.loads(r.text))
                print(json_response['nodeRef'][24:])
                radicate.set_cmis_id(json_response['nodeRef'][24:])

            except Exception as Error:

                print("Ha ocurrido un error al guardar el archivo")
                print(Error)

            url = reverse('correspondence:detail_radicate', kwargs={'pk': radicate.pk})
            return HttpResponseRedirect(url)
        else:
            print("Invalid create radicate form")
            return render(request,'correspondence/create_radicate.html',context={'form':form,'person':person})
    else:
        form = RadicateForm(initial={'person':person.id})
        # form.fields['address'].choices = person.get_addresses()
        # form.fields['address'].initial = [1]
        # print(person.get_addresses())
        form.person = person

    return render(request,'correspondence/create_radicate.html',context={'form':form,'person':person})


class RadicateList(ListView):
    model = Radicate
    context_object_name = 'radicates'

    def get_queryset(self):
        queryset = super(RadicateList, self).get_queryset()
        queryset = queryset.filter(current_user=self.request.user)
        return queryset


class CurrentUserUpdate(UpdateView):
    model = Radicate
    template_name_suffix = '_currentuser_update_form'
    form_class = ChangeCurrentUserForm


def edit_radicate(request,id):
    radicate = get_object_or_404(Radicate,id=id)
    form = RadicateForm(instance=radicate)
    return render(request,'correspondence/create_radicate.html',context={'form':form,'person':radicate.person})


class RadicateDetailView(DetailView):
    model = Radicate


def detail_radicate_cmis(request,cmis_id):
    radicate = get_object_or_404(Radicate,cmis_id=cmis_id)
    return render(request,'correspondence/radicate_detail.html',context={'radicate':radicate})


def proyect_answer(request,pk):
    radicate = get_object_or_404(Radicate,id=pk)
    response_file = None
    answer = ''


    if request.method == 'POST':
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        doc=Document(os.path.join(BASE_DIR,'media/template.docx'))
        print(os.path.join(BASE_DIR,'media/template.docx'))


        Dictionary = {
            "*RAD_N*":datetime.now().strftime("%Y%m%d%H%M%S"),
            "*NOMBRES*": str(radicate.person),
            "*CIUDAD*": str(radicate.person.city),
            "*DIRECCION*": str(radicate.person.address)+" - "+str(radicate.person.city),
            "*EMAIL*":str(radicate.person.email),
            "*ASUNTO*": "RESPUESTA "+str(radicate.subject),
            '*FECHA*':datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            '*ANEXO*':'Imágenes',
            "*TEXTO*":str(request.POST.get("answer")).replace("\n",""),
            "*NOMBRES_REMITENTE*":str(radicate.current_user.first_name)+" "+str(radicate.current_user.last_name)
            }

        for i in Dictionary:
            for p in doc.paragraphs:
                if p.text.find(i)>=0:
                    p.text=p.text.replace(i,Dictionary[i])

        doc.save(os.path.join(BASE_DIR,'media/output.docx'))

        files = {'files':open(os.path.join(BASE_DIR,'media/output.docx'),'rb')}

        response = requests.post(
            settings.CONVERT_URL,
            files=files
        )


        with open(os.path.join(BASE_DIR,'media/response.pdf'),'wb') as f:
            f.write(response.content)

        response_file = 'media/response.pdf'
        answer = str(request.POST.get("answer")).replace("\n","")

    return render(request,'correspondence/radicate_answer.html',{'radicate':radicate,'response_file':response_file,'answer':answer})


# PERSONS Views
class PersonCreateView(CreateView):
    model = Person
    form_class = PersonForm


class PersonDetailView(DetailView):
    model = Person

class PersonUpdateView(UpdateView):
    model = Person
    form_class = PersonForm

    # Charts
def charts(request):
    return render(request,'correspondence/charts.html',context={})
