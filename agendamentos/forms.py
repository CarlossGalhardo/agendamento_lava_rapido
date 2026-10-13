from django import forms
from .models import Agendamento, Servico, ConfiguracaoLavaRapido
from .utils import verificar_vaga_disponivel


class AgendamentoClienteForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = [
            'nome_cliente',
            'telefone_cliente',
            'modelo_carro',
            'placa_carro',
            'servico',
            'data',
            'horario',
            'observacoes',
        ]
        widgets = {
            'nome_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Carlos Alberto da Silva',
                'required': True
            }),
            'telefone_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: (11) 98765-4321',
                'id': 'id_telefone_cliente',
                'required': True
            }),
            'modelo_carro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Honda Civic 2022 Preto',
                'required': True
            }),
            'placa_carro': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'Ex: BRA2E19 (opcional)',
                'maxlength': '10'
            }),
            'servico': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'data': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
                'id': 'input-data-agendamento'
            }),
            'horario': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True,
                'id': 'input-horario-agendamento'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Alguma observação especial sobre o veículo ou serviço? (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servico'].queryset = Servico.objects.filter(ativo=True)
        self.fields['servico'].empty_label = "Selecione o serviço desejado"

    def clean(self):
        cleaned_data = super().clean()
        data = cleaned_data.get('data')
        horario = cleaned_data.get('horario')

        if data and horario:
            if not verificar_vaga_disponivel(data, horario):
                raise forms.ValidationError(
                    "Desculpe! O horário selecionado não está mais disponível para esta data. Por favor, escolha outro horário."
                )

        return cleaned_data


class AgendamentoAdminForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = [
            'nome_cliente',
            'telefone_cliente',
            'modelo_carro',
            'placa_carro',
            'servico',
            'data',
            'horario',
            'status',
            'observacoes',
        ]
        widgets = {
            'nome_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo_carro': forms.TextInput(attrs={'class': 'form-control'}),
            'placa_carro': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'servico': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'horario': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ConfiguracaoForm(forms.ModelForm):
    dias_semana_choices = [
        ('0', 'Segunda-feira'),
        ('1', 'Terça-feira'),
        ('2', 'Quarta-feira'),
        ('3', 'Quinta-feira'),
        ('4', 'Sexta-feira'),
        ('5', 'Sábado'),
        ('6', 'Domingo'),
    ]

    dias_selecionados = forms.MultipleChoiceField(
        choices=dias_semana_choices,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input me-1'}),
        required=False,
        label="Dias de Funcionamento"
    )

    class Meta:
        model = ConfiguracaoLavaRapido
        fields = [
            'nome_empresa',
            'telefone',
            'whatsapp',
            'endereco',
            'horario_abertura',
            'horario_fechamento',
            'intervalo_minutos',
            'vagas_simultaneas',
            'pausa_almoco_inicio',
            'pausa_almoco_fim',
        ]
        widgets = {
            'nome_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'horario_abertura': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'horario_fechamento': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'intervalo_minutos': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 5}),
            'vagas_simultaneas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'pausa_almoco_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'pausa_almoco_fim': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.dias_funcionamento:
            self.fields['dias_selecionados'].initial = [
                d.strip() for d in self.instance.dias_funcionamento.split(',') if d.strip()
            ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        dias = self.cleaned_data.get('dias_selecionados', [])
        instance.dias_funcionamento = ','.join(dias)
        if commit:
            instance.save()
        return instance


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['nome', 'descricao', 'preco', 'duracao_minutos', 'icone', 'ativo', 'ordem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50'}),
            'duracao_minutos': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 5}),
            'icone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: bi-droplet-half, bi-stars, bi-gem'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
        }
