import json
import urllib.request
import urllib.error
from datetime import date, datetime
from django.core.cache import cache


WMO_CODES = {
    0: ("Céu Limpo / Ensolarado", "bi-sun-fill", "text-warning", False),
    1: ("Predomínio de Sol", "bi-sun-fill", "text-warning", False),
    2: ("Parcialmente Nublado", "bi-cloud-sun-fill", "text-warning", False),
    3: ("Nublado", "bi-clouds-fill", "text-secondary", False),
    45: ("Nevoeiro", "bi-cloud-fog2-fill", "text-secondary", False),
    48: ("Nevoeiro com Geada", "bi-cloud-fog2-fill", "text-secondary", False),
    51: ("Garoa Leve", "bi-cloud-drizzle-fill", "text-info", True),
    53: ("Garoa Moderada", "bi-cloud-drizzle-fill", "text-info", True),
    55: ("Garoa Densa", "bi-cloud-drizzle-fill", "text-info", True),
    61: ("Chuva Fraca", "bi-cloud-rain-fill", "text-primary", True),
    63: ("Chuva Moderada", "bi-cloud-rain-fill", "text-primary", True),
    65: ("Chuva Forte", "bi-cloud-rain-heavy-fill", "text-primary", True),
    71: ("Neve Leve", "bi-snow", "text-info", True),
    80: ("Pancadas de Chuva Leves", "bi-cloud-rain-fill", "text-primary", True),
    81: ("Pancadas de Chuva Moderadas", "bi-cloud-rain-heavy-fill", "text-primary", True),
    82: ("Pancadas de Chuva Violentas", "bi-cloud-rain-heavy-fill", "text-danger", True),
    95: ("Tempestade com Raios", "bi-cloud-lightning-rain-fill", "text-danger", True),
    96: ("Tempestade com Granizo", "bi-cloud-lightning-rain-fill", "text-danger", True),
    99: ("Tempestade Severa", "bi-cloud-lightning-rain-fill", "text-danger", True),
}


def _buscar_dados_open_meteo(latitude: float, longitude: float):
    """
    Realiza a requisição HTTP à API externa Open-Meteo com cache local de 1 hora.
    """
    cache_key = f"open_meteo_{latitude}_{longitude}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone=America%2FSao_Paulo"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'LavaRapidoApp/1.0 (trabalho-faculdade)'}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status == 200:
                raw_json = response.read().decode('utf-8')
                dados = json.loads(raw_json)
                cache.set(cache_key, dados, timeout=3600)  # 1 hora de cache
                return dados
    except Exception as e:
        # Falha silenciosa com log para nunca travar a aplicação principal
        return None

    return None


def obter_previsao_tempo(data_alvo: date, latitude: float = -23.5505, longitude: float = -46.6333):
    """
    Retorna a previsão do tempo para uma data específica consumindo a API externa Open-Meteo.
    """
    dados = _buscar_dados_open_meteo(latitude, longitude)
    data_str = data_alvo.strftime('%Y-%m-%d')

    if not dados or 'daily' not in dados:
        return {
            'disponivel': False,
            'motivo': 'Serviço de meteorologia temporariamente indisponível.'
        }

    daily = dados['daily']
    datas = daily.get('time', [])

    if data_str not in datas:
        return {
            'disponivel': False,
            'motivo': 'Previsão disponível apenas para os próximos 7 dias.'
        }

    idx = datas.index(data_str)
    code = daily.get('weather_code', [0])[idx]
    temp_max = daily.get('temperature_2m_max', [0])[idx]
    temp_min = daily.get('temperature_2m_min', [0])[idx]
    prob_chuva = daily.get('precipitation_probability_max', [0])[idx] or 0

    condicao, icone, cor_icone, alerta_chuva_code = WMO_CODES.get(
        code,
        ("Tempo Estável", "bi-cloud-sun", "text-secondary", False)
    )

    # Se a probabilidade de chuva for >= 40%, gera alerta para o lava rápido
    alerta_chuva = alerta_chuva_code or (prob_chuva >= 40)

    # Dica inteligente de lavagem baseada no clima
    if prob_chuva >= 60:
        dica = f"🌧️ Previsão de chuva ({prob_chuva}% de chance). Dica: Aplique Cera Protetora Hidrorrepelente para repelir a água e proteger a pintura!"
    elif prob_chuva >= 30:
        dica = f"⛅ Possibilidade de chuva isolada ({prob_chuva}%). Uma boa opção para lavagem externa rápida."
    else:
        dica = f"☀️ Dia com sol e tempo firme ({prob_chuva}% de chuva). Clima ideal para uma Lavagem Completa e Polimento!"

    return {
        'disponivel': True,
        'data': data_str,
        'condicao': condicao,
        'icone': icone,
        'cor_icone': cor_icone,
        'temp_max': round(temp_max),
        'temp_min': round(temp_min),
        'probabilidade_chuva': prob_chuva,
        'alerta_chuva': alerta_chuva,
        'dica': dica
    }


def obter_previsao_semanal(latitude: float = -23.5505, longitude: float = -46.6333):
    """
    Retorna a lista com a previsão dos próximos 7 dias para o dashboard do dono.
    """
    dados = _buscar_dados_open_meteo(latitude, longitude)
    if not dados or 'daily' not in dados:
        return []

    daily = dados['daily']
    datas = daily.get('time', [])
    previsoes = []

    for i in range(min(7, len(datas))):
        d_str = datas[i]
        d_obj = datetime.strptime(d_str, '%Y-%m-%d').date()
        code = daily.get('weather_code', [0])[i]
        temp_max = daily.get('temperature_2m_max', [0])[i]
        temp_min = daily.get('temperature_2m_min', [0])[i]
        prob_chuva = daily.get('precipitation_probability_max', [0])[i] or 0

        condicao, icone, cor_icone, _ = WMO_CODES.get(
            code,
            ("Tempo Estável", "bi-cloud-sun", "text-secondary", False)
        )

        dias_curtos = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        dia_semana_nome = dias_curtos[d_obj.weekday()]

        previsoes.append({
            'data_str': d_str,
            'dia_mes': d_obj.strftime('%d/%m'),
            'dia_semana': dia_semana_nome,
            'condicao': condicao,
            'icone': icone,
            'cor_icone': cor_icone,
            'temp_max': round(temp_max),
            'temp_min': round(temp_min),
            'prob_chuva': prob_chuva,
        })

    return previsoes
