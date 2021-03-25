from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.urls import reverse


# Create your models here.



# Office attributes related to the person working Office
class Office(models.Model):
    name = models.CharField(max_length=256)
    abbr = models.CharField(max_length=10)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    date_created = models.DateField(auto_now=True)
    date_closed = models.DateTimeField(auto_now=False, null=True, blank=True)
    is_active = models.BooleanField()

    def __str__(self):
        return str(self.name)+' - '+str(self.abbr)


# UserProfileInfo, has one user for extend the basic user info
class UserProfileInfo(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_user')
    office = models.ForeignKey('Office', on_delete=models.CASCADE, related_name='user_profiles', default=False)
    def __str__(self):
        return self.user.first_name+' '+self.user.last_name+' ('+self.office.name+') '

class Country(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey('Country',on_delete=models.CASCADE,related_name='states',default=False)
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=128)
    state = models.ForeignKey('State',on_delete=models.CASCADE,related_name='cities')
    city_id = models.IntegerField(default=False)

    def __str__(self):
        return self.name+' / '+self.state.name


# Generic person class, attributes for senders and recievers
class Person(models.Model):
    DOCUMENT_TYPES = [
        ('CC','Cédula de ciudadanía'),
        ('NIT','Número único de identificación tributaria'),
        ('TI','Tarjeta de identidad'),
        ('CE','Cédula de extranjería')
    ]

    document_type = models.TextField(max_length=60,choices=DOCUMENT_TYPES,null=True)
    document_number = models.CharField(max_length=25,null=True,unique=True,db_index=True)
    email = models.EmailField(null=True)
    name = models.CharField(max_length=256,null=False,blank=False,unique=True)
    city = models.ForeignKey('City',on_delete=models.CASCADE,related_name='persons',default=False)
    address = models.CharField(max_length=256,null=True,blank=True,unique=False)
    parent = models.ForeignKey('self',on_delete=models.CASCADE,blank=True,null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('correspondence:detail_person',args=[str(self.id)])

    def get_addresses(self):
        address_list = []
        address_list.append((1,self.address))
        if hasattr(self.parent, 'address'):
            address_list.append((2,self.parent.address))

        return address_list


class Raft(models.Model):
    description = models.TextField(max_length=64,null=False)
    init_date = models.DateField(null=False)
    end_date = models.DateField(null=False)

    def __str__(self):
        return self.description


class Subraft(models.Model):
    raft = models.ForeignKey('Raft', on_delete=models.CASCADE, related_name='subseries')
    description = models.TextField(max_length=64, null=False)
    init_date = models.DateField(null=False)
    end_date = models.DateField(null=False)

    def __str__(self):
        return self.raft.description+' / '+self.description


class Doctype(models.Model):
    sub_raft = models.ForeignKey('Subraft', on_delete=models.CASCADE, related_name='tipos_doc')
    description = models.TextField(max_length=64, null=False)
    init_date = models.DateField(null=False)
    end_date = models.DateField(null=False)

    def __str__(self):
        return self.sub_raft.raft.description+' / '+self.sub_raft.description+' / '+self.description


class Radicate(models.Model):

    RADICATE_TYPES = [
        ('EN','Entrada'),
        ('SA','Salida'),
        ('ME','Memorando')
    ]

    RECEPTION_MODES = [
        ('VA','Valija'),
        ('EL','Electrónico'),
        ('472','472'),
        ('PR','Presencial')
    ]

    number = models.TextField(max_length=30,null=False,db_index=True)
    subject = models.TextField(max_length=256,null=True)
    annexes = models.TextField(max_length=256,null=True)
    observation = models.TextField(max_length=256,null=True)
    type = models.TextField(max_length=60,null=False,choices=RADICATE_TYPES,default='EN')
    date_radicated = models.DateTimeField(default=datetime.now,db_index=True)
    creator = models.ForeignKey(UserProfileInfo,on_delete=models.CASCADE,related_name='radicates_creator',default=False)
    person = models.ForeignKey('Person',on_delete=models.CASCADE,related_name='radicates_person',default=False)
    current_user = models.ForeignKey(UserProfileInfo,on_delete=models.CASCADE,related_name='radicates_user',default=False)
    reception_mode = models.TextField(max_length=10,choices=RECEPTION_MODES,default='PR')
    document_file = models.FileField(upload_to="uploads/",blank=False,null=False)
    cmis_id = models.TextField(max_length=128,null=True)
    use_parent_address = models.BooleanField(default=False)
    office = models.ForeignKey('Office', on_delete=models.CASCADE, related_name='radicates_office',default='1')
    doctype = models.ForeignKey('Doctype', on_delete=models.CASCADE, related_name='radicates_doctype', blank=True, null=True)


    def __str__(self):
        return str(self.number)

    def get_absolute_url(self):
        return reverse('correspondence:detail_radicate',args=[str(self.id)])

    def set_cmis_id(self,cmis_id):
        self.cmis_id = cmis_id
        self.save()

def get_first_name(self):
      return self.first_name+' '+self.last_name

User.add_to_class("__str__", get_first_name)
