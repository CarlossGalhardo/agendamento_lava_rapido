from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import time
from agendamentos.models import Servico, ConfiguracaoLavaRapido, Agendamento


class Command(BaseCommand):
    help = "Popula o banco de dados com serviços padrão, configurações e usuário administrador"

    def handle(self, *args, **options):
        # 1. Cria usuário dono/admin se não existir
        admin_username = "admin"
        admin_password = "admin123"
        admin_email = "admin@lavarapido.com"

        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name="Carlos",
                last_name="Gerente"
            )
            self.stdout.write(self.style.SUCCESS(f"Usuário admin criado: login='{admin_username}', senha='{admin_password}'"))
        else:
            self.stdout.write(self.style.WARNING(f"Usuário '{admin_username}' já existe."))

        # 2. Configurações do Lava Rápido
        config, created = ConfiguracaoLavaRapido.objects.get_or_create(id=1)
        if created or not config.nome_empresa:
            config.nome_empresa = "Lava Rápido AutoBrilho"
            config.telefone = "(11) 98765-4321"
            config.whatsapp = "5511987654321"
            config.endereco = "Av. Brasil, 1500 - Centro"
            config.horario_abertura = time(8, 0)
            config.horario_fechamento = time(18, 0)
            config.intervalo_minutos = 60
            config.vagas_simultaneas = 2
            config.dias_funcionamento = "0,1,2,3,4,5"  # Seg a Sáb
            config.pausa_almoco_inicio = time(12, 0)
            config.pausa_almoco_fim = time(13, 0)
            config.save()
            self.stdout.write(self.style.SUCCESS("Configurações iniciais criadas."))

        # 3. Serviços padrão
        servicos_iniciais = [
            {
                "nome": "Lavagem Simples",
                "descricao": "Lavagem externa com xampu neutro, secagem e pretinho nos pneus.",
                "preco": Decimal("40.00"),
                "duracao_minutos": 45,
                "icone": "bi-droplet-half",
                "ordem": 1
            },
            {
                "nome": "Lavagem Completa",
                "descricao": "Lavagem externa, aspiração interna, higienização dos painéis e aromatização.",
                "preco": Decimal("70.00"),
                "duracao_minutos": 60,
                "icone": "bi-stars",
                "ordem": 2
            },
            {
                "nome": "Lavagem com Cera Protetora",
                "descricao": "Lavagem completa + aplicação manual de cera de carnaúba para alto brilho e proteção.",
                "preco": Decimal("110.00"),
                "duracao_minutos": 75,
                "icone": "bi-shield-shaded",
                "ordem": 3
            },
            {
                "nome": "Higienização Interna Completa",
                "descricao": "Limpeza profunda de estofados/bancos de couro, carpetes, teto e dutos de ar.",
                "preco": Decimal("220.00"),
                "duracao_minutos": 120,
                "icone": "bi-sparkles",
                "ordem": 4
            },
            {
                "nome": "Polimento e Cristalização",
                "descricao": "Correção de pintura, remoção de micro-riscos e vitrificação/selamento de alto nível.",
                "preco": Decimal("350.00"),
                "duracao_minutos": 180,
                "icone": "bi-gem",
                "ordem": 5
            },
        ]

        for s_data in servicos_iniciais:
            servico, s_created = Servico.objects.get_or_create(
                nome=s_data["nome"],
                defaults=s_data
            )
            if s_created:
                self.stdout.write(self.style.SUCCESS(f"Serviço '{servico.nome}' criado."))

        self.stdout.write(self.style.SUCCESS("Banco de dados inicializado com sucesso!"))
