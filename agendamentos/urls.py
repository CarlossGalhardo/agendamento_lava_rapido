from django.urls import path
from . import views

urlpatterns = [
    # Área Pública (Clientes)
    path('', views.home, name='home'),
    path('sucesso/<str:codigo>/', views.sucesso_agendamento, name='sucesso_agendamento'),
    
    # APIs para JavaScript Dinâmico
    path('api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
    path('api/consultar-agendamento/', views.api_consultar_agendamento, name='api_consultar_agendamento'),
    
    # Autenticação Dono
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Painel do Dono
    path('painel/', views.dashboard_view, name='dashboard'),
    path('painel/agendamentos/novo/', views.dashboard_novo_agendamento, name='dashboard_novo_agendamento'),
    path('painel/agendamentos/<int:pk>/status/', views.api_atualizar_status, name='api_atualizar_status'),
    path('painel/agendamentos/<int:pk>/excluir/', views.api_excluir_agendamento, name='api_excluir_agendamento'),
    path('painel/configuracoes/', views.configuracoes_view, name='configuracoes'),
    path('painel/servicos/', views.servicos_view, name='servicos'),
    path('painel/servicos/<int:pk>/toggle/', views.servico_toggle_view, name='servico_toggle'),
    path('painel/servicos/<int:pk>/excluir/', views.servico_excluir_view, name='servico_excluir'),
]
