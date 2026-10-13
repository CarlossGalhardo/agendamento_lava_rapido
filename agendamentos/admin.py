from django.contrib import admin
from .models import Servico, ConfiguracaoLavaRapido, Agendamento


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'duracao_minutos', 'ativo', 'ordem')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    list_editable = ('preco', 'ativo', 'ordem')


@admin.register(ConfiguracaoLavaRapido)
class ConfiguracaoLavaRapidoAdmin(admin.ModelAdmin):
    list_display = ('nome_empresa', 'telefone', 'horario_abertura', 'horario_fechamento', 'vagas_simultaneas')

    def has_add_permission(self, request):
        # Allow only one configuration row
        return not ConfiguracaoLavaRapido.objects.exists()


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome_cliente', 'telefone_cliente', 'modelo_carro', 'servico', 'data', 'horario', 'status')
    list_filter = ('status', 'data', 'servico')
    search_fields = ('codigo', 'nome_cliente', 'telefone_cliente', 'modelo_carro', 'placa_carro')
    list_editable = ('status',)
    date_hierarchy = 'data'
