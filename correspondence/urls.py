from django.conf.urls import url
from correspondence import views
from django.urls import path

import correspondence.api_views

app_name = 'correspondence'

urlpatterns = [
    path('api/v1/radicates/', correspondence.api_views.RadicateList.as_view(), name='search_radicates'),
    url(r'^$', views.index, name='index'),
    path('search_names/', views.search_names, name='search_names'),
    path('search_content/', views.search_by_content, name='search_by_content'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
    path('radicate/create/<int:person>/', views.create_radicate, name='create_radicate'),
    path('radicate/list/', views.RadicateList.as_view(), name='list_radicate'),
    path('radicate/<int:pk>/', views.RadicateDetailView.as_view(), name="detail_radicate"),
    path('radicate_detail/<str:cmis_id>/', views.detail_radicate_cmis, name="detail_radicate_cmis"),
    path('edit_radicate/<int:id>/', views.edit_radicate, name='edit_radicate'),
    path('current_user/<int:pk>/', views.CurrentUserUpdate.as_view(), name='current_user'),
    path('person/create/', views.PersonCreateView.as_view(), name='create_person'),
    path('person/<int:pk>/', views.PersonDetailView.as_view(), name='detail_person'),
    path('edit_person/<int:pk>/', views.PersonUpdateView.as_view(), name='edit_person'),
    path('register/', views.register, name='register'),
    path('user_login/', views.user_login, name='user_login'),
    path('charts/', views.charts, name='charts'),
    path('proyect_answer/<int:pk>/', views.proyect_answer, name='proyect_answer'),
]
