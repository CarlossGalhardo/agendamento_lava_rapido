from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Servico, ConfiguracaoLavaRapido, Agendamento
from .utils import gerar_horarios_disponiveis, verificar_vaga_disponivel
from .weather import obter_previsao_tempo, obter_previsao_semanal


class LavaRapidoTestCase(TestCase):
    def setUp(self):
        # Cria usuário dono/admin
        self.owner = User.objects.create_user(
            username='dono_teste',
            password='senha123',
            first_name='Carlos'
        )

        # Configurações do lava rápido
        self.config = ConfiguracaoLavaRapido.objects.create(
            id=1,
            nome_empresa="Lava Rápido Teste",
            telefone="(11) 99999-8888",
            whatsapp="5511999998888",
            endereco="Rua Teste, 123",
            horario_abertura=time(8, 0),
            horario_fechamento=time(18, 0),
            intervalo_minutos=60,
            vagas_simultaneas=2,
            dias_funcionamento="0,1,2,3,4,5",  # Seg a Sáb
            pausa_almoco_inicio=time(12, 0),
            pausa_almoco_fim=time(13, 0)
        )

        # Cria serviços
        self.servico = Servico.objects.create(
            nome="Lavagem Completa",
            descricao="Externa e interna",
            preco=Decimal("70.00"),
            duracao_minutos=60,
            ativo=True
        )

        self.client = Client()

    def test_geracao_horarios_disponiveis(self):
        """Verifica se os horários são gerados respeitando horário de almoço e vagas"""
        amanha = timezone.localdate() + timedelta(days=1)
        # Se amanhã for domingo (weekday 6), pula para segunda
        if amanha.weekday() == 6:
            amanha += timedelta(days=1)

        resultado = gerar_horarios_disponiveis(amanha)
        self.assertTrue(resultado['valido'])
        self.assertGreater(len(resultado['horarios']), 0)

        # Garante que 12:00 (almoço) não esteja na lista de horários
        horarios_str = [h['horario'] for h in resultado['horarios']]
        self.assertNotIn('12:00', horarios_str)
        self.assertIn('08:00', horarios_str)
        self.assertIn('09:00', horarios_str)

    def test_bloqueio_data_retroativa(self):
        """Verifica se datas passadas são bloqueadas"""
        ontem = timezone.localdate() - timedelta(days=1)
        resultado = gerar_horarios_disponiveis(ontem)
        self.assertFalse(resultado['valido'])

    def test_agendamento_cliente_sucesso(self):
        """Testa o fluxo de agendamento feito pelo cliente"""
        futuro = timezone.localdate() + timedelta(days=2)
        if futuro.weekday() == 6:
            futuro += timedelta(days=1)

        payload = {
            'nome_cliente': 'Maria Santos',
            'telefone_cliente': '(11) 98765-4321',
            'modelo_carro': 'Toyota Corolla 2021',
            'placa_carro': 'ABC-1234',
            'servico': self.servico.id,
            'data': futuro.strftime('%Y-%m-%d'),
            'horario': '10:00',
            'observacoes': 'Carro com um pouco de barro',
        }

        response = self.client.post(reverse('home'), data=payload)
        self.assertEqual(response.status_code, 302)

        # Verifica se foi salvo no banco
        agendamento = Agendamento.objects.filter(nome_cliente='Maria Santos').first()
        self.assertIsNotNone(agendamento)
        self.assertEqual(agendamento.modelo_carro, 'Toyota Corolla 2021')
        self.assertEqual(agendamento.status, 'pendente')
        self.assertTrue(agendamento.codigo.startswith('LR-'))

    def test_limite_capacidade_vagas(self):
        """Garante que não é permitido agendar quando as vagas estão esgotadas"""
        futuro = timezone.localdate() + timedelta(days=3)
        if futuro.weekday() == 6:
            futuro += timedelta(days=1)

        horario = time(14, 0)

        # Cria 2 agendamentos para esgotar as 2 vagas
        Agendamento.objects.create(
            nome_cliente="Cliente 1",
            telefone_cliente="11999990001",
            modelo_carro="Carro 1",
            servico=self.servico,
            data=futuro,
            horario=horario,
            status='confirmado'
        )
        Agendamento.objects.create(
            nome_cliente="Cliente 2",
            telefone_cliente="11999990002",
            modelo_carro="Carro 2",
            servico=self.servico,
            data=futuro,
            horario=horario,
            status='pendente'
        )

        # Não deve haver vaga disponível agora
        vaga_livre = verificar_vaga_disponivel(futuro, horario)
        self.assertFalse(vaga_livre)

    def test_consulta_agendamento_api(self):
        """Verifica a busca do cliente por código de reserva"""
        futuro = timezone.localdate() + timedelta(days=1)
        if futuro.weekday() == 6:
            futuro += timedelta(days=1)

        ag = Agendamento.objects.create(
            nome_cliente="Pedro Silva",
            telefone_cliente="(11) 97777-6666",
            modelo_carro="VW Gol",
            servico=self.servico,
            data=futuro,
            horario=time(9, 0),
            status='pendente'
        )

        response = self.client.get(reverse('api_consultar_agendamento'), {'termo': ag.codigo})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['encontrado'])
        self.assertEqual(data['agendamentos'][0]['cliente'], 'Pedro Silva')

    def test_acesso_painel_requer_login(self):
        """Painel administrativo deve redirecionar usuários não autenticados"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_dono_visualiza_e_atualiza_status(self):
        """Dono autenticado acessa o dashboard e atualiza o status de um agendamento"""
        self.client.login(username='dono_teste', password='senha123')

        ag = Agendamento.objects.create(
            nome_cliente="Ana Lima",
            telefone_cliente="(11) 91111-2222",
            modelo_carro="Jeep Renegade",
            servico=self.servico,
            data=timezone.localdate(),
            horario=time(11, 0),
            status='pendente'
        )

        # Acessa painel
        resp_dashboard = self.client.get(reverse('dashboard'))
        self.assertEqual(resp_dashboard.status_code, 200)
        self.assertContains(resp_dashboard, "Ana Lima")
        self.assertContains(resp_dashboard, "Jeep Renegade")

        # Atualiza status via POST
        url_status = reverse('api_atualizar_status', kwargs={'pk': ag.pk})
        resp_status = self.client.post(
            f"{url_status}?ajax=1",
            data={'status': 'confirmado'},
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(resp_status.status_code, 200)
        ag.refresh_from_db()
        self.assertEqual(ag.status, 'confirmado')

    # ==========================================
    # TESTES DA INTEGRAÇÃO COM API EXTERNA (Open-Meteo)
    # ==========================================

    def _mock_open_meteo_payload(self):
        """Retorna um payload fake simulando a resposta da API Open-Meteo."""
        hoje = timezone.localdate()
        datas = [(hoje + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        return {
            "daily": {
                "time": datas,
                "weather_code": [0, 61, 2, 3, 80, 0, 1],
                "temperature_2m_max": [32.0, 22.5, 28.0, 26.0, 24.0, 33.0, 31.0],
                "temperature_2m_min": [20.0, 18.0, 19.0, 17.0, 16.0, 21.0, 20.0],
                "precipitation_probability_max": [5, 80, 20, 10, 60, 0, 5],
            }
        }

    @patch('agendamentos.weather._buscar_dados_open_meteo')
    def test_previsao_tempo_dia_ensolarado(self, mock_buscar):
        """Verifica retorno correto para o dia de hoje (WMO code 0 = ensolarado, 5% chuva)"""
        mock_buscar.return_value = self._mock_open_meteo_payload()

        hoje = timezone.localdate()
        resultado = obter_previsao_tempo(hoje, latitude=-23.5505, longitude=-46.6333)

        self.assertTrue(resultado['disponivel'])
        self.assertIn('condicao', resultado)
        self.assertIn('temp_max', resultado)
        self.assertEqual(resultado['probabilidade_chuva'], 5)
        self.assertFalse(resultado['alerta_chuva'])

    @patch('agendamentos.weather._buscar_dados_open_meteo')
    def test_previsao_tempo_dia_com_chuva(self, mock_buscar):
        """Verifica alerta de chuva e dica inteligente para dia chuvoso (amanhã = 80%)"""
        mock_buscar.return_value = self._mock_open_meteo_payload()

        amanha = timezone.localdate() + timedelta(days=1)
        resultado = obter_previsao_tempo(amanha, latitude=-23.5505, longitude=-46.6333)

        self.assertTrue(resultado['disponivel'])
        self.assertEqual(resultado['probabilidade_chuva'], 80)
        self.assertTrue(resultado['alerta_chuva'])
        self.assertIn('Cera Protetora', resultado['dica'])

    @patch('agendamentos.weather._buscar_dados_open_meteo')
    def test_previsao_indisponivel_alem_de_7_dias(self, mock_buscar):
        """Verifica comportamento ao consultar data além dos 7 dias retornados"""
        mock_buscar.return_value = self._mock_open_meteo_payload()

        data_distante = timezone.localdate() + timedelta(days=15)
        resultado = obter_previsao_tempo(data_distante, latitude=-23.5505, longitude=-46.6333)

        self.assertFalse(resultado['disponivel'])

    @patch('agendamentos.weather._buscar_dados_open_meteo')
    def test_previsao_retorna_none_quando_api_falha(self, mock_buscar):
        """Verifica fallback gracioso quando a API externa está indisponível"""
        mock_buscar.return_value = None

        resultado = obter_previsao_tempo(timezone.localdate(), latitude=-23.5505, longitude=-46.6333)

        self.assertFalse(resultado['disponivel'])
        self.assertIn('motivo', resultado)

    @patch('agendamentos.weather._buscar_dados_open_meteo')
    def test_previsao_semanal_retorna_lista_de_7_dias(self, mock_buscar):
        """Verifica se a previsão semanal retorna exatamente 7 dias com campos corretos"""
        mock_buscar.return_value = self._mock_open_meteo_payload()

        resultado = obter_previsao_semanal(latitude=-23.5505, longitude=-46.6333)

        self.assertEqual(len(resultado), 7)
        self.assertIn('dia_semana', resultado[0])
        self.assertIn('temp_max', resultado[0])
        self.assertIn('prob_chuva', resultado[0])

    @patch('agendamentos.weather._buscar_dados_open_meteo')
    def test_api_horarios_inclui_previsao_tempo(self, mock_buscar):
        """Verifica se o endpoint de horários livres retorna o campo previsao_tempo da API"""
        mock_buscar.return_value = self._mock_open_meteo_payload()

        amanha = timezone.localdate() + timedelta(days=1)
        if amanha.weekday() == 6:
            amanha += timedelta(days=1)

        response = self.client.get(
            reverse('api_horarios_disponiveis'),
            {'data': amanha.strftime('%Y-%m-%d')}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('previsao_tempo', data)
        self.assertIn('disponivel', data['previsao_tempo'])
