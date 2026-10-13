import json
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q

from .models import Servico, ConfiguracaoLavaRapido, Agendamento
from .forms import AgendamentoClienteForm, AgendamentoAdminForm, ConfiguracaoForm, ServicoForm
from .utils import gerar_horarios_disponiveis, verificar_vaga_disponivel


# ==========================================
# ÁREA PÚBLICA / CLIENTES
# ==========================================

def home(request):
    config = ConfiguracaoLavaRapido.get_config()
    servicos = Servico.objects.filter(ativo=True)
    hoje = timezone.localdate()

    # Prepara os próximos 14 dias para navegação rápida de datas
    dias_semana_curtos = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    dias_abertos = config.dias_funcionamento_lista()
    
    proximos_dias = []
    for i in range(14):
        d = hoje + timedelta(days=i)
        is_aberto = d.weekday() in dias_abertos
        proximos_dias.append({
            'data_str': d.strftime('%Y-%m-%d'),
            'dia_mes': d.strftime('%d/%m'),
            'dia_semana': dias_semana_curtos[d.weekday()],
            'is_hoje': (i == 0),
            'aberto': is_aberto,
        })

    if request.method == 'POST':
        form = AgendamentoClienteForm(request.POST)
        if form.is_valid():
            agendamento = form.save()
            messages.success(request, "Agendamento realizado com sucesso!")
            return redirect('sucesso_agendamento', codigo=agendamento.codigo)
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        form = AgendamentoClienteForm(initial={'data': hoje})

    context = {
        'config': config,
        'servicos': servicos,
        'form': form,
        'hoje_str': hoje.strftime('%Y-%m-%d'),
        'proximos_dias': proximos_dias,
    }
    return render(request, 'agendamentos/index.html', context)


def api_horarios_disponiveis(request):
    """
    API chamada via JavaScript quando o cliente clica ou seleciona uma data.
    Retorna os horários e se cada um está disponível ou lotado.
    """
    data_str = request.GET.get('data')
    if not data_str:
        return JsonResponse({'valido': False, 'motivo': 'Data não fornecida.'}, status=400)

    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'valido': False, 'motivo': 'Formato de data inválido (use YYYY-MM-DD).'}, status=400)

    resultado = gerar_horarios_disponiveis(data_obj)
    return JsonResponse(resultado)


def api_consultar_agendamento(request):
    """
    Permite ao cliente consultar o status do seu agendamento informando
    o código da reserva ou o telefone de contato.
    """
    termo = request.GET.get('termo', '').strip()
    if not termo:
        return JsonResponse({'encontrado': False, 'mensagem': 'Informe o código ou telefone.'})

    # Remove caracteres não numéricos se for telefone
    termo_limpo = ''.join(filter(str.isdigit, termo))

    filtros = Q(codigo__iexact=termo)
    if termo_limpo:
        filtros |= Q(telefone_cliente__icontains=termo_limpo)

    agendamentos = Agendamento.objects.filter(filtros).select_related('servico').order_by('-data', '-horario')[:5]

    if not agendamentos.exists():
        return JsonResponse({'encontrado': False, 'mensagem': 'Nenhum agendamento encontrado.'})

    itens = []
    for ag in agendamentos:
        itens.append({
            'codigo': ag.codigo,
            'cliente': ag.nome_cliente,
            'modelo_carro': ag.modelo_carro,
            'placa': ag.placa_carro or 'Não informada',
            'servico': ag.servico.nome if ag.servico else 'Personalizado',
            'preco': f"R$ {ag.servico.preco:.2f}" if ag.servico else '-',
            'data': ag.data.strftime('%d/%m/%Y'),
            'horario': ag.horario.strftime('%H:%M'),
            'status': ag.status,
            'status_display': ag.get_status_display(),
        })

    return JsonResponse({'encontrado': True, 'agendamentos': itens})


def sucesso_agendamento(request, codigo):
    agendamento = get_object_or_404(Agendamento, codigo=codigo)
    config = ConfiguracaoLavaRapido.get_config()
    
    # Mensagem pré-formatada para o cliente enviar no WhatsApp do Lava Rápido se desejar
    msg_zap = (
        f"Olá, fiz o agendamento no {config.nome_empresa}!\n"
        f"📋 Código: {agendamento.codigo}\n"
        f"👤 Nome: {agendamento.nome_cliente}\n"
        f"🚗 Carro: {agendamento.modelo_carro}\n"
        f"📅 Data: {agendamento.data.strftime('%d/%m/%Y')} às {agendamento.horario.strftime('%H:%M')}\n"
        f"💧 Serviço: {agendamento.servico.nome if agendamento.servico else 'Geral'}"
    )
    import urllib.parse
    zap_url = f"https://wa.me/{config.whatsapp}?text={urllib.parse.quote(msg_zap)}"

    context = {
        'agendamento': agendamento,
        'config': config,
        'zap_url': zap_url,
    }
    return render(request, 'agendamentos/sucesso.html', context)


# ==========================================
# ÁREA ADMINISTRATIVA / DONO DO LAVA RÁPIDO
# ==========================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        usuario = request.POST.get('username')
        senha = request.POST.get('password')
        user = authenticate(request, username=usuario, password=senha)
        if user is not None:
            login(request, user)
            messages.success(request, f"Bem-vindo(a), {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Usuário ou senha inválidos. Tente novamente.")

    return render(request, 'agendamentos/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu da sua conta.")
    return redirect('login')


@login_required
def dashboard_view(request):
    hoje = timezone.localdate()
    config = ConfiguracaoLavaRapido.get_config()

    # Filtros
    filtro_data = request.GET.get('data_filtro', 'hoje')
    filtro_status = request.GET.get('status', 'todos')
    busca = request.GET.get('busca', '').strip()
    data_especifica = request.GET.get('data_especifica', '')

    queryset = Agendamento.objects.select_related('servico').all()

    # Aplica filtro de data
    if filtro_data == 'hoje':
        queryset = queryset.filter(data=hoje)
    elif filtro_data == 'amanha':
        queryset = queryset.filter(data=hoje + timedelta(days=1))
    elif filtro_data == 'semana':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        queryset = queryset.filter(data__range=[inicio_semana, fim_semana])
    elif filtro_data == 'mes':
        queryset = queryset.filter(data__year=hoje.year, data__month=hoje.month)
    elif filtro_data == 'especifica' and data_especifica:
        try:
            d_esp = datetime.strptime(data_especifica, '%Y-%m-%d').date()
            queryset = queryset.filter(data=d_esp)
        except ValueError:
            pass
    # 'todos' não filtra por data

    # Aplica filtro de status
    if filtro_status in ['pendente', 'confirmado', 'concluido', 'cancelado']:
        queryset = queryset.filter(status=filtro_status)

    # Aplica busca textual
    if busca:
        queryset = queryset.filter(
            Q(nome_cliente__icontains=busca) |
            Q(telefone_cliente__icontains=busca) |
            Q(modelo_carro__icontains=busca) |
            Q(placa_carro__icontains=busca) |
            Q(codigo__icontains=busca)
        )

    # Ordenação
    agendamentos = queryset.order_by('data', 'horario')

    # Métricas / Estatísticas para o topo do Dashboard
    agendamentos_hoje_qs = Agendamento.objects.filter(data=hoje)
    total_hoje = agendamentos_hoje_qs.count()
    pendentes_total = Agendamento.objects.filter(status='pendente').count()
    confirmados_hoje = agendamentos_hoje_qs.filter(status='confirmado').count()
    concluidos_hoje = agendamentos_hoje_qs.filter(status='concluido').count()

    # Faturamento estimado hoje (concluídos e confirmados)
    faturamento_hoje = agendamentos_hoje_qs.filter(
        status__in=['concluido', 'confirmado']
    ).aggregate(total=Sum('servico__preco'))['total'] or 0

    # Faturamento do mês
    faturamento_mes = Agendamento.objects.filter(
        data__year=hoje.year,
        data__month=hoje.month,
        status__in=['concluido', 'confirmado']
    ).aggregate(total=Sum('servico__preco'))['total'] or 0

    # Formulário para criar agendamento manual caso o dono receba cliente presencial ou por telefone
    admin_form = AgendamentoAdminForm(initial={'data': hoje, 'status': 'confirmado'})

    context = {
        'agendamentos': agendamentos,
        'config': config,
        'filtro_data': filtro_data,
        'filtro_status': filtro_status,
        'busca': busca,
        'data_especifica': data_especifica,
        'hoje_str': hoje.strftime('%Y-%m-%d'),
        'total_hoje': total_hoje,
        'pendentes_total': pendentes_total,
        'confirmados_hoje': confirmados_hoje,
        'concluidos_hoje': concluidos_hoje,
        'faturamento_hoje': faturamento_hoje,
        'faturamento_mes': faturamento_mes,
        'admin_form': admin_form,
    }
    return render(request, 'agendamentos/dashboard.html', context)


@login_required
def api_atualizar_status(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        if novo_status in ['pendente', 'confirmado', 'concluido', 'cancelado']:
            agendamento.status = novo_status
            agendamento.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
                return JsonResponse({
                    'sucesso': True,
                    'status': agendamento.status,
                    'status_display': agendamento.get_status_display()
                })
            messages.success(request, f"Agendamento {agendamento.codigo} alterado para {agendamento.get_status_display()}!")
        else:
            messages.error(request, "Status inválido.")
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def api_excluir_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    if request.method == 'POST':
        codigo = agendamento.codigo
        agendamento.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'sucesso': True})
        messages.success(request, f"Agendamento {codigo} excluído com sucesso.")
    return redirect('dashboard')


@login_required
def dashboard_novo_agendamento(request):
    """Permite ao dono criar um agendamento rápido pelo painel"""
    if request.method == 'POST':
        form = AgendamentoAdminForm(request.POST)
        if form.is_valid():
            ag = form.save()
            messages.success(request, f"Agendamento {ag.codigo} criado para {ag.nome_cliente}!")
        else:
            messages.error(request, "Erro ao criar agendamento. Verifique os campos.")
    return redirect('dashboard')


@login_required
def configuracoes_view(request):
    config = ConfiguracaoLavaRapido.get_config()
    if request.method == 'POST':
        form = ConfiguracaoForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações atualizadas com sucesso!")
            return redirect('configuracoes')
        else:
            messages.error(request, "Erro ao salvar configurações. Verifique os dados inseridos.")
    else:
        form = ConfiguracaoForm(instance=config)

    return render(request, 'agendamentos/configuracoes.html', {'form': form, 'config': config})


@login_required
def servicos_view(request):
    servicos = Servico.objects.all()
    form = ServicoForm()

    if request.method == 'POST':
        form = ServicoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço adicionado com sucesso!")
            return redirect('servicos')
        else:
            messages.error(request, "Erro ao adicionar serviço.")

    return render(request, 'agendamentos/servicos.html', {'servicos': servicos, 'form': form})


@login_required
def servico_toggle_view(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    servico.ativo = not servico.ativo
    servico.save()
    status_str = "ativado" if servico.ativo else "desativado"
    messages.info(request, f"Serviço '{servico.nome}' {status_str}.")
    return redirect('servicos')


@login_required
def servico_excluir_view(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    nome = servico.nome
    servico.delete()
    messages.success(request, f"Serviço '{nome}' excluído com sucesso.")
    return redirect('servicos')
