from datetime import datetime, date, time, timedelta
from django.utils import timezone
from .models import ConfiguracaoLavaRapido, Agendamento, Servico


def gerar_horarios_disponiveis(data_selecionada: date):
    """
    Calcula e retorna a lista de horários e a disponibilidade para uma determinada data.
    """
    config = ConfiguracaoLavaRapido.get_config()
    hoje = timezone.localdate()
    agora = timezone.localtime().time()

    # Validação 1: Data retroativa
    if data_selecionada < hoje:
        return {
            "valido": False,
            "motivo": "Esta data já passou. Por favor, escolha a data de hoje ou uma data futura.",
            "horarios": []
        }

    # Validação 2: Dia de funcionamento
    dias_abertos = config.dias_funcionamento_lista()
    dia_semana = data_selecionada.weekday()  # 0=Segunda, 6=Domingo
    nomes_dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

    if dia_semana not in dias_abertos:
        return {
            "valido": False,
            "motivo": f"O lava rápido não abre aos(às) {nomes_dias[dia_semana]}s. Escolha outro dia.",
            "horarios": []
        }

    # Construir grade de horários
    horarios_info = []
    
    # Converter para datetime para somar timedelta
    dummy_date = date(2000, 1, 1)
    abertura_dt = datetime.combine(dummy_date, config.horario_abertura)
    fechamento_dt = datetime.combine(dummy_date, config.horario_fechamento)
    intervalo = timedelta(minutes=max(15, config.intervalo_minutos))

    # Obter agendamentos já existentes para esta data
    agendamentos_dia = Agendamento.objects.filter(
        data=data_selecionada,
        status__in=['pendente', 'confirmado']
    ).values('horario')

    # Contagem de agendamentos por horário
    contagem_horarios = {}
    for ag in agendamentos_dia:
        h_str = ag['horario'].strftime('%H:%M')
        contagem_horarios[h_str] = contagem_horarios.get(h_str, 0) + 1

    current_dt = abertura_dt
    while current_dt + intervalo <= fechamento_dt:
        slot_time = current_dt.time()
        slot_str = slot_time.strftime('%H:%M')
        current_dt += intervalo

        # Verificar se está no intervalo de almoço
        no_almoco = False
        if config.pausa_almoco_inicio and config.pausa_almoco_fim:
            if config.pausa_almoco_inicio <= slot_time < config.pausa_almoco_fim:
                no_almoco = True

        if no_almoco:
            continue

        # Verificar se horário já passou (no caso de ser o dia de hoje)
        ja_passou = False
        if data_selecionada == hoje and slot_time <= agora:
            ja_passou = True

        ocupados = contagem_horarios.get(slot_str, 0)
        vagas_restantes = max(0, config.vagas_simultaneas - ocupados)
        esgotado = vagas_restantes <= 0

        disponivel = (not ja_passou) and (not esgotado)
        motivo = None
        if ja_passou:
            motivo = "Horário encerrado"
        elif esgotado:
            motivo = "Esgotado (sem vagas)"

        horarios_info.append({
            "horario": slot_str,
            "disponivel": disponivel,
            "vagas_totais": config.vagas_simultaneas,
            "vagas_restantes": vagas_restantes,
            "motivo": motivo
        })

    return {
        "valido": True,
        "motivo": None,
        "dia_semana": nomes_dias[dia_semana],
        "data_formatada": data_selecionada.strftime('%d/%m/%Y'),
        "horarios": horarios_info
    }


def verificar_vaga_disponivel(data_agendamento: date, horario_agendamento: time) -> bool:
    """
    Verifica se ainda existe vaga disponível para o dia e horário especificados.
    """
    config = ConfiguracaoLavaRapido.get_config()
    hoje = timezone.localdate()
    agora = timezone.localtime().time()

    if data_agendamento < hoje:
        return False
    if data_agendamento == hoje and horario_agendamento <= agora:
        return False
    if data_agendamento.weekday() not in config.dias_funcionamento_lista():
        return False

    ocupados = Agendamento.objects.filter(
        data=data_agendamento,
        horario=horario_agendamento,
        status__in=['pendente', 'confirmado']
    ).count()

    return ocupados < config.vagas_simultaneas
