from typing import Dict

from django.shortcuts import render
from correspondence.forms import RadicateForm , SearchForm, UserForm,  UserProfileInfoForm, PersonForm, RecordForm, SearchContentForm, ChangeCurrentUserForm, ChangeRecordAssignedForm ,LoginForm
from datetime import datetime
from django.utils.timezone import get_current_timezone
from django.conf import settings
from correspondence.models import Radicate, Person, Record
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
from django.contrib.postgres.search import SearchVector, TrigramSimilarity, SearchQuery, SearchRank, SearchHeadline

from django.contrib import messages

import requests
import json
import os
from docx import Document
import logging

from pinax.eventlog.models import log, Log
logger = logging.getLogger(__name__)


from requests.auth import HTTPBasicAuth


# Index view

def index(request):
    return render(request,'correspondence/index.html',{})



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
            logger.error(user_form.errors,user_profile_form.errors)
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
    results = []
    response = None
    error = None
    cmis_id_list = []
    radicate_list = []
    search_results = {}
    qs = None

    if request.method == 'POST':
        form = SearchContentForm(data=request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            term = cleaned_data['term']
            headers: Dict[str, str] = {'Content-Type': 'application/json'}
            try:
                response = requests.post(
                    settings.ECM_SEARCH_URL,
                    json =dict(query=dict(query=term),
                            highlight=dict(
                            mergeContiguous=True, fragmentSize=150,
                            usePhraseHighlighter=True,
                            fields=[
                                dict(field="name", prefix="( ", postfix=" )"),
                                dict(field="content", prefix="( ", postfix=" )")
                            ])),
                    auth = HTTPBasicAuth(settings.ECM_USER, settings.ECM_PASSWORD),
                    headers=headers
                )

                # list of responses from ECM
                entries = response.json()['list']['entries']
                # list of cmis id's from response
                cmis_id_list=[ data['entry']['id'] for data in entries ]
                # list of radicates with the cmis id's
                radicate_list = Radicate.objects.filter(cmis_id__in=cmis_id_list).distinct()
                # list of cmis id's in efect in the radicates .
                cmis_filtered_ids = [ radicate.cmis_id for radicate in radicate_list ]


                # We made a dictionary with the results for send its to the template
                # first we add the search of the json part from the response
                for entry in entries:
                    if entry['entry']['id'] in cmis_filtered_ids:
                        search_results[entry['entry']['id']]={"search":entry['entry']['search']}

                # second we add the radicates to the dictionary with the cmis_id as key
                for radi in radicate_list:
                   search_results[radi.cmis_id]['radicate']=radi


                if radicate_list.count():
                   logger.info(results)
                else:
                    messages.info(request,"No se ha encontrado el término en el contenido")

            except Exception as inst:
                messages.error(request, "Ha occurrido un error al realizar la búsqueda, por favor intente más tarde")


            finally:
                # finally we search for results in the database

                vector = SearchVector('number', 'subject',  'person__name','person__document_number')
                query = SearchQuery(term)

                qs = Radicate.objects.annotate(rank=SearchRank(vector, query),
                    headline=SearchHeadline('subject',query,start_sel='<u>',stop_sel='</u>',)).filter(rank__gte=0.06).order_by('-rank')

                if not qs.count():
                    messages.info(request, "La búsqueda en la base de datos no obtuvo resultados")


    else:
        form = SearchContentForm()

    return render(request,'correspondence/content_search.html',context={'term':term,'results':search_results, 'db_results':qs ,'form':form})


# Search by names
@login_required
def search_names(request):

    if request.method == 'POST':
        form=SearchForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['item']
            qs = Person.objects.annotate(search=SearchVector('document_number','email','name','address','parent__name'),).filter(search=item)
            if not qs.count():
                messages.warning(request,"La búsqueda no obtuvo resultados")

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
            cleaned_data = form.cleaned_data
            form.document_file = request.FILES['document_file']
            now = datetime.now()
            instance.number = now.strftime("%Y%m%d%H%M%S")
            instance.creator = request.user.profile_user
            instance.current_user = request.user.profile_user
            instance.person = person
            radicate = form.save()


            log(
                user=request.user,
                action="RADICATE_CREATED",
                obj=radicate,
                extra={
                    "number": radicate.number
                }
            )

            url = settings.ECM_UPLOAD_URL
            auth = (settings.ECM_USER, settings.ECM_PASSWORD)
            files = {"filedata": open(os.path.join(BASE_DIR,radicate.document_file.path), "rb")}
            data = {"siteid": "rino", "containerid": "files"}

            try:
                r = requests.post(url, files=files, data=data, auth=auth)
                json_response =(json.loads(r.text))
                radicate.set_cmis_id(json_response['entry']['id'])

            except Exception as Error:

                logger.error(Error)
                messages.error(request,"Ha ocurrido un error al guardar el archivo en el gestor de contenido")

            messages.success(request,"El radicado se ha creado correctamente")
            url = reverse('correspondence:detail_radicate', kwargs={'pk': radicate.pk})
            return HttpResponseRedirect(url)
        else:
            logger.error("Invalid create radicate form")
            return render(request,'correspondence/create_radicate.html',context={'form':form,'person':person})
    else:
        form = RadicateForm(initial={'person':person.id})
        form.person = person

    return render(request,'correspondence/create_radicate.html',context={'form':form,'person':person})


class RadicateList(ListView):
    model = Radicate
    context_object_name = 'radicates'

    def get_queryset(self):
        queryset = super(RadicateList, self).get_queryset()
        queryset = queryset.filter(current_user=self.request.user.profile_user.pk)
        return queryset


class CurrentUserUpdate(UpdateView):
    model = Radicate
    template_name_suffix = '_currentuser_update_form'
    form_class = ChangeCurrentUserForm

class RecordAssignedUpdate(UpdateView):
    model = Radicate
    template_name_suffix = '_recordassigned_update_form'
    form_class = ChangeRecordAssignedForm

    def form_valid(self, form):
    
        response = super(RecordAssignedUpdate, self).form_valid(form)
        url = settings.ECM_RECORD_ASSIGN_URL + self.object.cmis_id + '/move'
        auth = (settings.ECM_USER, settings.ECM_PASSWORD)
        data = '{"targetParentId": "' + self.object.record.cmis_id + '"}' 

        try:
            r = requests.post(url, data=data, auth=auth)
            json_response =(json.loads(r.text))
            print(json_response)
            messages.success(self.request, "El archivo se ha guardado correctamente en el expediente")
            return response

        except Exception as Error:
            logger.error(Error)
            messages.error(self.request,"Ha ocurrido un error al actualizar el archivo en el gestor de contenido")
            self.object = None
            return self.form_invalid(form)


def edit_radicate(request,id):
    radicate = get_object_or_404(Radicate,id=id)
    form = RadicateForm(instance=radicate)
    return render(request,'correspondence/create_radicate.html',context={'form':form,'person':radicate.person})


class RadicateDetailView(DetailView):
    model = Radicate

    def get_context_data(self, **kwargs):
        context = super(RadicateDetailView, self).get_context_data(**kwargs)
        context['logs'] = Log.objects.all().filter(object_id=self.kwargs['pk'])
        return context


def detail_radicate_cmis(request,cmis_id):
    radicate = get_object_or_404(Radicate,cmis_id=cmis_id)
    logs = Log.objects.all().filter(object_id=radicate.pk)
    return render(request,'correspondence/radicate_detail.html',context={'radicate':radicate,'logs':logs})


def project_answer(request,pk):
    radicate = get_object_or_404(Radicate,id=pk)
    response_file = None
    answer = ''


    if request.method == 'POST':
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        doc=Document(os.path.join(BASE_DIR,'media/template.docx'))

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
            "*NOMBRES_REMITENTE*":str(radicate.current_user.user.first_name)+" "+str(radicate.current_user.user.last_name)
            }

        for i in Dictionary:
            for p in doc.paragraphs:
                if p.text.find(i)>=0:
                    p.text=p.text.replace(i,Dictionary[i])

        doc.save(os.path.join(BASE_DIR,'media/output.docx'))

        files = {'files':open(os.path.join(BASE_DIR,'media/output.docx'),'rb')}

        try:
            response = requests.post(
                settings.CONVERT_URL,
                files=files
            )
            with open(os.path.join(BASE_DIR, 'media/response.pdf'), 'wb') as f:
                f.write(response.content)

            response_file = 'media/response.pdf'
            answer = str(request.POST.get("answer")).replace("\n", "")


        except Exception as Error:
            logger.error(Error)
            messages.error(request, "Ha ocurrido un error al comunicarse con los servicios de conversión. Por favor informe al administrador del sistema")


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


# RECORDS Views
class RecordCreateView(CreateView):
    model = Record
    form_class = RecordForm

    def form_valid(self, form):

        response = super(RecordCreateView, self).form_valid(form)
        url = settings.ECM_RECORD_URL
        auth = (settings.ECM_USER, settings.ECM_PASSWORD)
        print(self.object)
        data = '{"name": "' + self.object.name + '", "nodeType": "cm:folder"}'

        try:
            r = requests.post(url, data=data, auth=auth)
            json_response =(json.loads(r.text))
            print(json_response)
            self.object.set_cmis_id(json_response['entry']['id'])
            messages.success(self.request, "El expediente se ha guardado correctamente")
            return response

        except Exception as Error:
            logger.error(Error)
            messages.error(self.request,"Ha ocurrido un error al crear el expediente en el gestor de contenido")
            self.object = None
            return self.form_invalid(form)



class RecordDetailView(DetailView):
    model = Record

class RecordUpdateView(UpdateView):
    model = Record
    form_class = RecordForm

    def form_valid(self, form):
    
        response = super(RecordUpdateView, self).form_valid(form)
        url = settings.ECM_RECORD_UPDATE_URL + self.object.cmis_id
        auth = (settings.ECM_USER, settings.ECM_PASSWORD)
        data = '{"name": "' + self.object.name + '"}' 

        try:
            r = requests.put(url, data=data, auth=auth)
            json_response =(json.loads(r.text))
            print(json_response)
            messages.success(self.request, "El expediente se ha guardado correctamente")
            return response

        except Exception as Error:
            logger.error(Error)
            messages.error(self.request,"Ha ocurrido un error al actualizar el expediente en el gestor de contenido")
            self.object = None
            return self.form_invalid(form)

class RecordListView(ListView):
    model = Record
    context_object_name = 'records'

    def get_queryset(self):
        queryset = super(RecordListView, self).get_queryset()
        return queryset

    # Charts
def charts(request):
    return render(request,'correspondence/charts.html',context={})
