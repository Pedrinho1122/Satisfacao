// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    updateDate();
    loadDashboardData();
    setInterval(loadDashboardData, 5000); // Atualizar a cada 5 segundos
});

// Atualizar data
function updateDate() {
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    const today = new Date().toLocaleDateString('pt-PT', options);
    document.getElementById('current-date').textContent = today;
}

// Carregar dados do dashboard
async function loadDashboardData() {
    await loadStats();
    await loadHistory();
}

// Carregar estatísticas
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        if (response.ok) {
            const stats = await response.json();
            
            // Atualizar números
            document.getElementById('stat-1').textContent = stats[1] || 0;
            document.getElementById('stat-2').textContent = stats[2] || 0;
            document.getElementById('stat-3').textContent = stats[3] || 0;
            
            const total = (stats[1] || 0) + (stats[2] || 0) + (stats[3] || 0);
            document.getElementById('stat-total').textContent = total;
            
            // Atualizar gráficos
            updateChart(stats, total);
        }
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

// Atualizar gráfico
function updateChart(stats, total) {
    if (total === 0) {
        for (let i = 1; i <= 3; i++) {
            document.getElementById(`bar-fill-${i}`).style.width = '0%';
            document.querySelector(`#bar-${i} .bar-label`).textContent = '0%';
        }
        return;
    }
    
    for (let i = 1; i <= 3; i++) {
        const count = stats[i] || 0;
        const percentage = Math.round((count / total) * 100);
        
        document.getElementById(`bar-fill-${i}`).style.width = percentage + '%';
        document.querySelector(`#bar-${i} .bar-label`).textContent = percentage + '%';
    }
}

// Carregar histórico
async function loadHistory() {
    try {
        const response = await fetch('/api/avaliacoes');
        if (response.ok) {
            const data = await response.json();
            const historyList = document.getElementById('history-list');
            
            if (data.avaliacoes && data.avaliacoes.length > 0) {
                historyList.innerHTML = '';
                
                const tipos = {
                    1: { emoji: '😀', label: 'Muito Satisfeito' },
                    2: { emoji: '🙂', label: 'Satisfeito' },
                    3: { emoji: '😞', label: 'Insatisfeito' }
                };
                
                data.avaliacoes.forEach(avaliacao => {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    
                    const tipo = tipos[avaliacao.tipo];
                    
                    item.innerHTML = `
                        <div class="history-item-left">
                            <span class="history-emoji">${tipo.emoji}</span>
                            <div>
                                <div class="history-label">${tipo.label}</div>
                                <div class="history-time">#${avaliacao.sequential_number} às ${avaliacao.avaliacao_time}</div>
                            </div>
                        </div>
                    `;
                    
                    historyList.appendChild(item);
                });
            } else {
                historyList.innerHTML = '<p class="empty-message">Nenhuma avaliação registada hoje</p>';
            }
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
    }
}
