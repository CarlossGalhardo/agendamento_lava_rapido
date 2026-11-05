/**
 * agendamento.js - Interatividade, comunicação assíncrona, validações e melhorias de UX
 */

document.addEventListener('DOMContentLoaded', function () {
    
    // ==========================================
    // 0. HELPER DE NOTIFICAÇÃO (TOAST)
    // ==========================================
    function notificar(mensagem, tipo = 'warning') {
        if (typeof window.mostrarToast === 'function') {
            window.mostrarToast(mensagem, tipo);
        } else {
            alert(mensagem);
        }
    }

    // ==========================================
    // 1. ESTADO GLOBAL DO AGENDAMENTO
    // ==========================================
    let estado = {
        servicoId: null,
        servicoNome: '',
        servicoPreco: 0,
        servicoDuracao: 0,
        data: '',
        horario: '',
        carro: '',
        placa: '',
        placaValida: true
    };

    // Elementos do DOM
    const form = document.getElementById('formAgendamento');
    const inputData = document.getElementById('input-data-agendamento');
    const inputHorario = document.getElementById('input-horario-agendamento');
    const inputTelefone = document.getElementById('id_telefone_cliente');
    const inputModeloCarro = document.getElementById('id_modelo_carro');
    const inputPlaca = document.getElementById('id_placa_carro');
    const placaFeedback = document.getElementById('placaFeedback');
    const selectServico = document.getElementById('id_servico');

    const slotsLoading = document.getElementById('slotsLoading');
    const slotsContainer = document.getElementById('slotsContainer');
    const slotsGrid = document.getElementById('slotsGrid');
    const slotsMensagemErro = document.getElementById('slotsMensagemErro');
    const slotsMensagemTexto = document.getElementById('slotsMensagemTexto');
    const dataSelecionadaLabel = document.getElementById('dataSelecionadaLabel');

    // Elementos do Resumo
    const resumoServicoNome = document.getElementById('resumoServicoNome');
    const resumoServicoPreco = document.getElementById('resumoServicoPreco');
    const resumoServicoDuracao = document.getElementById('resumoServicoDuracao');
    const resumoData = document.getElementById('resumoData');
    const resumoHorario = document.getElementById('resumoHorario');
    const resumoVeiculo = document.getElementById('resumoVeiculo');

    // ==========================================
    // 2. SELEÇÃO DE SERVIÇO
    // ==========================================
    const serviceCards = document.querySelectorAll('.service-card');

    function selecionarServico(card) {
        serviceCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        estado.servicoId = card.getAttribute('data-id');
        estado.servicoNome = card.getAttribute('data-nome');
        estado.servicoPreco = parseFloat(card.getAttribute('data-preco') || 0);
        estado.servicoDuracao = card.getAttribute('data-duracao');

        // Atualiza campo select oculto do Django
        if (selectServico) {
            selectServico.value = estado.servicoId;
        }

        // Atualiza Resumo
        if (resumoServicoNome) resumoServicoNome.textContent = estado.servicoNome;
        if (resumoServicoPreco) resumoServicoPreco.textContent = `R$ ${estado.servicoPreco.toFixed(2).replace('.', ',')}`;
        if (resumoServicoDuracao) resumoServicoDuracao.textContent = `~${estado.servicoDuracao} min`;
    }

    serviceCards.forEach(card => {
        card.addEventListener('click', function () {
            selecionarServico(this);
        });
    });

    // Inicializa o primeiro serviço como selecionado
    if (serviceCards.length > 0) {
        selecionarServico(serviceCards[0]);
    }

    // ==========================================
    // 3. SELEÇÃO DE DATA & CARREGAMENTO DE SLOTS
    // ==========================================
    const datePills = document.querySelectorAll('.date-pill');

    function selecionarData(dataStr, elementoPill = null) {
        estado.data = dataStr;
        if (inputData) inputData.value = dataStr;

        // Atualiza pílulas visuais
        datePills.forEach(p => p.classList.remove('active'));
        if (elementoPill) {
            elementoPill.classList.add('active');
        } else {
            const pillCorrespondente = document.querySelector(`.date-pill[data-date="${dataStr}"]`);
            if (pillCorrespondente) pillCorrespondente.classList.add('active');
        }

        // Atualiza label formatado
        const partes = dataStr.split('-');
        if (partes.length === 3) {
            const dataFormatada = `${partes[2]}/${partes[1]}/${partes[0]}`;
            if (dataSelecionadaLabel) dataSelecionadaLabel.textContent = `Data: ${dataFormatada}`;
            if (resumoData) resumoData.textContent = dataFormatada;
        }

        // Limpa horário anterior
        estado.horario = '';
        if (inputHorario) inputHorario.value = '';
        if (resumoHorario) resumoHorario.textContent = 'Selecione um horário';

        // Dispara requisição assíncrona para buscar horários
        carregarHorariosDisponiveis(dataStr);
    }

    datePills.forEach(pill => {
        pill.addEventListener('click', function () {
            if (this.disabled) return;
            const dataStr = this.getAttribute('data-date');
            selecionarData(dataStr, this);
        });
    });

    if (inputData) {
        inputData.addEventListener('change', function () {
            if (this.value) {
                selecionarData(this.value);
            }
        });
    }

    // ==========================================
    // 4. API ASSÍNCRONA DE HORÁRIOS LIVRES
    // ==========================================
    function carregarHorariosDisponiveis(dataStr) {
        if (slotsLoading) slotsLoading.classList.remove('d-none');
        if (slotsContainer) slotsContainer.classList.add('d-none');
        if (slotsMensagemErro) slotsMensagemErro.classList.add('d-none');
        if (slotsGrid) slotsGrid.innerHTML = '';

        fetch(`/api/horarios-disponiveis/?data=${encodeURIComponent(dataStr)}`)
            .then(response => response.json())
            .then(data => {
                if (slotsLoading) slotsLoading.classList.add('d-none');

                if (!data.valido) {
                    if (slotsMensagemErro && slotsMensagemTexto) {
                        slotsMensagemTexto.textContent = data.motivo || 'Nenhum horário disponível para esta data.';
                        slotsMensagemErro.classList.remove('d-none');
                    }
                    return;
                }

                if (!data.horarios || data.horarios.length === 0) {
                    if (slotsMensagemErro && slotsMensagemTexto) {
                        slotsMensagemTexto.textContent = 'Não há horários de funcionamento configurados para este dia.';
                        slotsMensagemErro.classList.remove('d-none');
                    }
                    return;
                }

                // Renderiza os horários disponíveis
                renderizarSlots(data.horarios);
                if (slotsContainer) slotsContainer.classList.remove('d-none');

                // Renderiza a previsão do tempo da API externa
                if (data.previsao_tempo) {
                    renderizarPrevisaoTempo(data.previsao_tempo);
                } else {
                    const cardPrevisao = document.getElementById('cardPrevisaoTempo');
                    if (cardPrevisao) cardPrevisao.classList.add('d-none');
                }
            })
            .catch(error => {
                console.error('Erro ao buscar horários:', error);
                if (slotsLoading) slotsLoading.classList.add('d-none');
                if (slotsMensagemErro && slotsMensagemTexto) {
                    slotsMensagemTexto.textContent = 'Erro ao consultar horários. Verifique sua conexão e tente novamente.';
                    slotsMensagemErro.classList.remove('d-none');
                }
            });
    }

    function renderizarSlots(horarios) {
        if (!slotsGrid) return;
        slotsGrid.innerHTML = '';

        horarios.forEach(slot => {
            const col = document.createElement('div');
            col.className = 'col-4 col-sm-3 col-md-2';

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn slot-btn w-100 d-flex flex-column align-items-center justify-content-center';
            btn.setAttribute('data-horario', slot.horario);

            let statusTexto = '';
            if (!slot.disponivel) {
                btn.disabled = true;
                statusTexto = `<small class="badge bg-secondary-subtle text-secondary small p-1 mt-1" style="font-size: 0.65rem;">${slot.motivo || 'Lotado'}</small>`;
            } else {
                statusTexto = `<small class="badge bg-success-subtle text-success small p-1 mt-1" style="font-size: 0.65rem;">${slot.vagas_restantes} vaga${slot.vagas_restantes > 1 ? 's' : ''}</small>`;
            }

            btn.innerHTML = `
                <span class="fs-6">${slot.horario}</span>
                ${statusTexto}
            `;

            if (slot.disponivel) {
                btn.addEventListener('click', function () {
                    selecionarHorario(slot.horario, btn);
                });
            }

            col.appendChild(btn);
            slotsGrid.appendChild(col);
        });
    }

    function selecionarHorario(horarioStr, btnElement) {
        document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
        btnElement.classList.add('selected');

        estado.horario = horarioStr;
        if (inputHorario) inputHorario.value = horarioStr;
        if (resumoHorario) resumoHorario.textContent = `às ${horarioStr} horas`;
    }

    function renderizarPrevisaoTempo(previsao) {
        const cardPrevisao = document.getElementById('cardPrevisaoTempo');
        if (!cardPrevisao) return;

        if (!previsao || !previsao.disponivel) {
            cardPrevisao.classList.add('d-none');
            return;
        }

        const icone = document.getElementById('climaIcone');
        const condicao = document.getElementById('climaCondicao');
        const tempMax = document.getElementById('climaTempMax');
        const tempMin = document.getElementById('climaTempMin');
        const probChuva = document.getElementById('climaProbChuva');
        const dicaTexto = document.getElementById('climaDicaTexto');

        if (icone) {
            icone.className = `bi ${previsao.icone || 'bi-cloud-sun-fill'} fs-2 ${previsao.cor_icone || 'text-warning'}`;
        }
        if (condicao) condicao.textContent = previsao.condicao || 'Tempo Estável';
        if (tempMax) tempMax.textContent = `${previsao.temp_max}°C`;
        if (tempMin) tempMin.textContent = `${previsao.temp_min}°C`;
        if (probChuva) probChuva.textContent = `${previsao.probabilidade_chuva}%`;
        if (dicaTexto) dicaTexto.textContent = previsao.dica || 'Consulte os horários abaixo.';

        cardPrevisao.classList.remove('d-none');
    }

    // Inicializa a data atual ao abrir a página
    if (inputData && inputData.value) {
        selecionarData(inputData.value);
    }

    // ==========================================
    // 5. MÁSCARA E VALIDAÇÃO DE PLACA (MERCOSUL & TRADICIONAL)
    // ==========================================
    function processarPlaca(valorBruto) {
        const limpo = valorBruto.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 7);
        if (!limpo) {
            return { formatado: '', tipo: null, valido: true, incompleto: false, preenchido: false };
        }

        const padraoMercosulCarro = /^[A-Z]{3}[0-9][A-Z][0-9]{2}$/;
        const padraoMercosulMoto = /^[A-Z]{3}[0-9]{2}[A-Z][0-9]$/;
        const padraoTradicional = /^[A-Z]{3}[0-9]{4}$/;

        let formatado = limpo;
        let tipo = 'Desconhecido';
        let valido = false;
        let incompleto = (limpo.length < 7);

        const c4 = limpo[4]; // 5º caractere
        const c5 = limpo[5]; // 6º caractere

        // Se o 5º caractere for letra, é formato Mercosul de Automóvel (ex: BRA2E19)
        if (limpo.length >= 5 && isNaN(c4)) {
            formatado = limpo;
            tipo = 'Mercosul';
            valido = padraoMercosulCarro.test(limpo);
        }
        // Se o 6º caractere for letra, é formato Mercosul de Moto (ex: BRA22E1)
        else if (limpo.length >= 6 && isNaN(c5)) {
            formatado = limpo;
            tipo = 'Mercosul Moto';
            valido = padraoMercosulMoto.test(limpo);
        }
        // Caso contrário, segue formato Tradicional brasileiro (ex: ABC-1234)
        else if (limpo.length > 3) {
            formatado = limpo.slice(0, 3) + '-' + limpo.slice(3, 7);
            tipo = 'Padrão Tradicional';
            valido = padraoTradicional.test(limpo);
        } else {
            formatado = limpo;
            tipo = 'Placa';
        }

        return { formatado, tipo, valido, incompleto, preenchido: true };
    }

    function atualizarResumoVeiculo() {
        if (!resumoVeiculo) return;
        const modelo = (inputModeloCarro && inputModeloCarro.value.trim()) || '';
        const placa = (inputPlaca && inputPlaca.value.trim()) || '';
        if (modelo) {
            resumoVeiculo.textContent = placa ? `${modelo} (${placa})` : modelo;
        } else {
            resumoVeiculo.textContent = 'Aguardando preenchimento';
        }
    }

    if (inputPlaca) {
        inputPlaca.addEventListener('input', function () {
            const resultado = processarPlaca(this.value);
            this.value = resultado.formatado;
            estado.placa = resultado.formatado;

            if (!resultado.preenchido) {
                // Campo opcional vazio
                this.classList.remove('is-valid', 'is-invalid');
                if (placaFeedback) placaFeedback.innerHTML = '';
                estado.placaValida = true;
            } else if (resultado.valido) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
                if (placaFeedback) {
                    placaFeedback.innerHTML = `
                        <span class="badge bg-success-subtle text-success border border-success-subtle d-inline-flex align-items-center gap-1">
                            <i class="bi bi-patch-check-fill"></i> ${resultado.tipo} válida
                        </span>
                    `;
                }
                estado.placaValida = true;
            } else {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
                if (placaFeedback) {
                    const motivo = resultado.incompleto ? 'incompleta' : 'formato inválido';
                    placaFeedback.innerHTML = `
                        <span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle d-inline-flex align-items-center gap-1">
                            <i class="bi bi-exclamation-circle-fill"></i> ${resultado.tipo} ${motivo}
                        </span>
                    `;
                }
                estado.placaValida = false;
            }

            atualizarResumoVeiculo();
        });
    }

    if (inputModeloCarro) {
        inputModeloCarro.addEventListener('input', atualizarResumoVeiculo);
    }

    // ==========================================
    // 6. MÁSCARA DE TELEFONE (WHATSAPP)
    // ==========================================
    if (inputTelefone) {
        inputTelefone.addEventListener('input', function (e) {
            let x = e.target.value.replace(/\D/g, '').match(/(\d{0,2})(\d{0,5})(\d{0,4})/);
            if (!x[2]) {
                e.target.value = x[1] ? `(${x[1]}` : '';
            } else if (!x[3]) {
                e.target.value = `(${x[1]}) ${x[2]}`;
            } else {
                e.target.value = `(${x[1]}) ${x[2]}-${x[3]}`;
            }
        });
    }

    // ==========================================
    // 7. VALIDAÇÃO ANTES DO SUBMIT (COM TOASTS)
    // ==========================================
    if (form) {
        form.addEventListener('submit', function (e) {
            if (!estado.servicoId) {
                notificar('Por favor, selecione um dos serviços de lavagem.', 'warning');
                e.preventDefault();
                return;
            }
            if (!estado.data) {
                notificar('Por favor, escolha uma data para o agendamento.', 'warning');
                e.preventDefault();
                return;
            }
            if (!inputHorario || !inputHorario.value) {
                notificar('Por favor, escolha um dos horários disponíveis na grade.', 'warning');
                e.preventDefault();
                return;
            }
            if (!inputModeloCarro || !inputModeloCarro.value.trim()) {
                notificar('Por favor, informe o modelo do seu veículo.', 'warning');
                if (inputModeloCarro) inputModeloCarro.focus();
                e.preventDefault();
                return;
            }
            if (!inputTelefone || !inputTelefone.value.trim() || inputTelefone.value.replace(/\D/g, '').length < 10) {
                notificar('Por favor, informe um telefone/WhatsApp válido com DDD.', 'warning');
                if (inputTelefone) inputTelefone.focus();
                e.preventDefault();
                return;
            }
            if (inputPlaca && inputPlaca.value.trim() && !estado.placaValida) {
                notificar('A placa informada está incompleta ou fora do padrão (Mercosul ou Tradicional).', 'warning');
                inputPlaca.focus();
                e.preventDefault();
                return;
            }

            const btnSubmit = document.getElementById('btnConfirmarAgendamento');
            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span> Processando agendamento...`;
            }
        });
    }

    // ==========================================
    // 8. BANNER DE ÚLTIMO AGENDAMENTO (LOCALSTORAGE)
    // ==========================================
    try {
        const agendamentoSalvo = JSON.parse(localStorage.getItem('ultimoAgendamentoLavaRapido') || 'null');
        if (agendamentoSalvo && agendamentoSalvo.codigo) {
            const banner = document.getElementById('bannerUltimoAgendamento');
            const bannerTexto = document.getElementById('bannerUltimoTexto');
            const bannerSubtexto = document.getElementById('bannerUltimoSubtexto');
            const btnVer = document.getElementById('btnVerUltimoAgendamento');
            const btnDispensar = document.getElementById('btnDispensarBanner');

            if (banner && bannerTexto && bannerSubtexto) {
                const dataDisp = agendamentoSalvo.dataFormatada || agendamentoSalvo.data;
                bannerTexto.textContent = `Olá, ${agendamentoSalvo.cliente || 'Cliente'}! Agendamento em ${dataDisp} às ${agendamentoSalvo.horario}`;
                bannerSubtexto.textContent = `Código: ${agendamentoSalvo.codigo} • Serviço: ${agendamentoSalvo.servico || ''} • Veículo: ${agendamentoSalvo.veiculo || ''}`;
                banner.classList.remove('d-none');

                if (btnVer) {
                    btnVer.addEventListener('click', function () {
                        const modalEl = document.getElementById('modalConsultarAgendamento');
                        const inputTermo = document.getElementById('inputConsultaTermo');
                        if (modalEl && window.bootstrap) {
                            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                            modal.show();
                            if (inputTermo) {
                                inputTermo.value = agendamentoSalvo.codigo;
                                buscarAgendamentos();
                            }
                        }
                    });
                }

                if (btnDispensar) {
                    btnDispensar.addEventListener('click', function () {
                        banner.classList.add('d-none');
                    });
                }
            }
        }
    } catch (e) {
        console.warn('Erro ao carregar agendamento do localStorage:', e);
    }

    // ==========================================
    // 9. CONSULTA DE AGENDAMENTOS (MODAL)
    // ==========================================
    const btnBuscar = document.getElementById('btnBuscarAgendamento');
    const inputTermo = document.getElementById('inputConsultaTermo');
    const containerResultados = document.getElementById('resultadoConsultaContainer');
    const loadingConsulta = document.getElementById('resultadoConsultaLoading');

    function buscarAgendamentos() {
        const termo = inputTermo ? inputTermo.value.trim() : '';
        if (!termo) {
            notificar('Digite o código da reserva ou seu telefone.', 'warning');
            return;
        }

        if (loadingConsulta) loadingConsulta.classList.remove('d-none');
        if (containerResultados) containerResultados.innerHTML = '';

        fetch(`/api/consultar-agendamento/?termo=${encodeURIComponent(termo)}`)
            .then(res => res.json())
            .then(data => {
                if (loadingConsulta) loadingConsulta.classList.add('d-none');

                if (!data.encontrado || !data.agendamentos || data.agendamentos.length === 0) {
                    if (containerResultados) {
                        containerResultados.innerHTML = `
                            <div class="alert alert-warning text-center rounded-3">
                                <i class="bi bi-search me-1"></i> Nenhum agendamento encontrado para "<strong>${termo}</strong>".
                            </div>
                        `;
                    }
                    return;
                }

                let html = '<div class="d-flex flex-column gap-3">';
                data.agendamentos.forEach(ag => {
                    let badgeClass = 'bg-secondary';
                    if (ag.status === 'pendente') badgeClass = 'bg-warning text-dark';
                    if (ag.status === 'confirmado') badgeClass = 'bg-info text-dark';
                    if (ag.status === 'concluido') badgeClass = 'bg-success text-white';
                    if (ag.status === 'cancelado') badgeClass = 'bg-danger text-white';

                    html += `
                        <div class="card border rounded-3 p-3 bg-light shadow-sm">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div>
                                    <span class="badge bg-dark font-monospace">${ag.codigo}</span>
                                    <h6 class="fw-bold mb-0 mt-1">${ag.modelo_carro}</h6>
                                </div>
                                <span class="badge ${badgeClass} px-3 py-1 rounded-pill">${ag.status_display}</span>
                            </div>
                            <div class="small text-muted mb-1">
                                <i class="bi bi-person"></i> ${ag.cliente}
                            </div>
                            <div class="small text-muted mb-2">
                                <i class="bi bi-droplet"></i> ${ag.servico} (${ag.preco})
                            </div>
                            <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                                <span class="fw-bold text-primary">
                                    <i class="bi bi-calendar-check"></i> ${ag.data} às ${ag.horario}
                                </span>
                                <a href="/sucesso/${ag.codigo}/" class="btn btn-outline-primary btn-sm rounded-pill">
                                    Ver Detalhes
                                </a>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';

                if (containerResultados) {
                    containerResultados.innerHTML = html;
                }
            })
            .catch(err => {
                console.error(err);
                if (loadingConsulta) loadingConsulta.classList.add('d-none');
                if (containerResultados) {
                    containerResultados.innerHTML = `
                        <div class="alert alert-danger text-center">
                            Erro ao consultar. Tente novamente mais tarde.
                        </div>
                    `;
                }
            });
    }

    if (btnBuscar) {
        btnBuscar.addEventListener('click', buscarAgendamentos);
    }
    if (inputTermo) {
        inputTermo.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                buscarAgendamentos();
            }
        });
    }

});
