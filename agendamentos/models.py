import uuid
from datetime import datetime, time, timedelta
from django.db import models


class Servico(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Serviço")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    preco = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Preço (R$)")
    duracao_minutos = models.PositiveIntegerField(default=45, verbose_name="Duração (min)")
    icone = models.CharField(max_length=50, default='bi-droplet-half', verbose_name="Ícone (Bootstrap Icons)")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem de Exibição")

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ['ordem', 'preco']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco:.2f}"


class ConfiguracaoLavaRapido(models.Model):
    nome_empresa = models.CharField(max_length=120, default="Lava Rápido AutoBrilho", verbose_name="Nome do Lava Rápido")
    telefone = models.CharField(max_length=25, default="(11) 98765-4321", verbose_name="Telefone de Contato")
    whatsapp = models.CharField(max_length=20, default="5511987654321", verbose_name="WhatsApp (apenas números com DDD)")
    endereco = models.CharField(max_length=255, default="Av. Brasil, 1500 - Centro", verbose_name="Endereço")
    horario_abertura = models.TimeField(default=time(8, 0), verbose_name="Horário de Abertura")
    horario_fechamento = models.TimeField(default=time(18, 0), verbose_name="Horário de Fechamento")
    intervalo_minutos = models.PositiveIntegerField(default=45, verbose_name="Intervalo entre Horários (minutos)")
    vagas_simultaneas = models.PositiveIntegerField(default=2, verbose_name="Vagas Simultâneas (Capacidade)")
    # 0 = Segunda, 1 = Terça, 2 = Quarta, 3 = Quinta, 4 = Sexta, 5 = Sábado, 6 = Domingo
    dias_funcionamento = models.CharField(
        max_length=50,
        default="0,1,2,3,4,5",
        verbose_name="Dias de Funcionamento (0=Seg até 6=Dom)",
        help_text="Separados por vírgula. Ex: 0,1,2,3,4,5 para Segunda a Sábado"
    )
    pausa_almoco_inicio = models.TimeField(null=True, blank=True, default=time(12, 0), verbose_name="Início Almoço")
    pausa_almoco_fim = models.TimeField(null=True, blank=True, default=time(13, 0), verbose_name="Fim Almoço")
    cidade = models.CharField(max_length=100, default="São Paulo - SP", verbose_name="Cidade")
    latitude = models.FloatField(default=-23.5505, verbose_name="Latitude (para Previsão do Tempo)")
    longitude = models.FloatField(default=-46.6333, verbose_name="Longitude (para Previsão do Tempo)")

    class Meta:
        verbose_name = "Configuração do Lava Rápido"
        verbose_name_plural = "Configurações do Lava Rápido"

    def __str__(self):
        return self.nome_empresa

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(id=1)
        return config

    def dias_funcionamento_lista(self):
        try:
            return [int(d.strip()) for d in self.dias_funcionamento.split(',') if d.strip().isdigit()]
        except Exception:
            return [0, 1, 2, 3, 4, 5]


class Agendamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    codigo = models.CharField(max_length=12, unique=True, editable=False, verbose_name="Código da Reserva")
    nome_cliente = models.CharField(max_length=120, verbose_name="Nome Completo")
    telefone_cliente = models.CharField(max_length=25, verbose_name="Contato / WhatsApp")
    modelo_carro = models.CharField(max_length=100, verbose_name="Modelo do Carro")
    placa_carro = models.CharField(max_length=15, blank=True, verbose_name="Placa do Carro")
    servico = models.ForeignKey(
        Servico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
        verbose_name="Serviço"
    )
    data = models.DateField(verbose_name="Data do Agendamento")
    horario = models.TimeField(verbose_name="Horário")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name="Status"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações do Cliente")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['data', 'horario']

    def __str__(self):
        return f"{self.codigo} - {self.nome_cliente} ({self.modelo_carro}) - {self.data.strftime('%d/%m/%Y')} {self.horario.strftime('%H:%M')}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"LR-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    @property
    def whatsapp_link(self):
        # Cleans phone to numbers only
        nums = ''.join(filter(str.isdigit, self.telefone_cliente))
        if len(nums) in (10, 11) and not nums.startswith('55'):
            nums = '55' + nums
        return f"https://wa.me/{nums}"
