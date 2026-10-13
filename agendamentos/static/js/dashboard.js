/**
 * dashboard.js - Ações dinâmicas e assíncronas do painel do dono do lava rápido
 */

document.addEventListener('DOMContentLoaded', function () {

    // Helper para obter CSRF Token do cookie ou input
    function getCsrfToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) return input.value;
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    // ==========================================
    // ATUALIZAÇÃO RÁPIDA DE STATUS VIA AJAX
    // ==========================================
    const botoesStatus = document.querySelectorAll('.btn-atualizar-status');

    botoesStatus.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const agendamentoId = this.getAttribute('data-id');
            const novoStatus = this.getAttribute('data-status');

            if (!agendamentoId || !novoStatus) return;

            const badgeElement = document.getElementById(`status-badge-${agendamentoId}`);
            if (badgeElement) {
                badgeElement.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span>`;
            }

            const formData = new FormData();
            formData.append('status', novoStatus);

            fetch(`/painel/agendamentos/${agendamentoId}/status/?ajax=1`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.sucesso) {
                    if (badgeElement) {
                        badgeElement.textContent = data.status_display;
                        badgeElement.className = `badge status-badge-${data.status} px-3 py-2 rounded-pill fw-semibold`;
                    }
                    // Recarrega suavemente a página após 400ms para atualizar métricas e botões
                    setTimeout(() => {
                        window.location.reload();
                    }, 400);
                } else {
                    alert('Erro ao atualizar status.');
                }
            })
            .catch(err => {
                console.error('Erro na requisição:', err);
                alert('Falha na comunicação com o servidor.');
            });
        });
    });

});
