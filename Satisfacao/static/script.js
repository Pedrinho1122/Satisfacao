// Inicializar
let isProcessing = false;
const TIMEOUT_MS = 2000; // 2 segundos de timeout
let currentDateKey = new Date().toDateString();

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    attachButtonListeners();
    startDailyResetWatcher();
});

// Adicionar listeners
function attachButtonListeners() {
    document.querySelectorAll('.satisfaction-button').forEach(button => {
        button.addEventListener('click', handleButtonClick);
    });
}

// Verificar mudança de dia e resetar contadores
function startDailyResetWatcher() {
    setInterval(() => {
        const newDateKey = new Date().toDateString();
        if (newDateKey !== currentDateKey) {
            currentDateKey = newDateKey;
            resetCounters();
            loadStats();
        }
    }, 60000); // verificar a cada 1 minuto
}

// Tratar clique
async function handleButtonClick(event) {
    // Verificar se já está a processar
    if (isProcessing) {
        return;
    }
    
    const button = event.currentTarget;
    const tipo = parseInt(button.dataset.tipo);
    
    // Bloquear botões
    isProcessing = true;
    disableAllButtons();
    
    try {
        const response = await fetch('/api/avaliar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tipo: tipo })
        });

        if (response.ok) {
            const data = await response.json();
            
            updateCounter(tipo, data.sequential_number);
            animateButton(button);
            showPopup(tipo, data.sequential_number, data.time);
        }
    } catch (error) {
        console.error('Erro:', error);
    } finally {
        // Reativar botões após timeout
        setTimeout(() => {
            isProcessing = false;
            enableAllButtons();
        }, TIMEOUT_MS);
    }
}

// Desativar todos os botões
function disableAllButtons() {
    document.querySelectorAll('.satisfaction-button').forEach(button => {
        button.disabled = true;
        button.style.opacity = '0.5';
        button.style.cursor = 'not-allowed';
    });
}

// Reativar todos os botões
function enableAllButtons() {
    document.querySelectorAll('.satisfaction-button').forEach(button => {
        button.disabled = false;
        button.style.opacity = '1';
        button.style.cursor = 'pointer';
    });
}

// Atualizar contador
function updateCounter(tipo, count) {
    document.getElementById(`count-${tipo}`).textContent = count;
}

// Reset visual dos contadores
function resetCounters() {
    document.getElementById('count-1').textContent = '0';
    document.getElementById('count-2').textContent = '0';
    document.getElementById('count-3').textContent = '0';
}

// Mostrar pop-up
function showPopup(tipo, sequential, time) {
    const tipos = {
        1: 'Muito Satisfeito',
        2: 'Satisfeito',
        3: 'Insatisfeito'
    };
    
    const popup = document.getElementById('info-popup');
    
    document.getElementById('popup-tipo').textContent = tipos[tipo];
    document.getElementById('popup-number').textContent = sequential;
    document.getElementById('popup-time').textContent = time;
    
    popup.classList.add('show');
    
    setTimeout(() => {
        popup.classList.remove('show');
    }, 3000);
}

// Animar botão
function animateButton(button) {
    button.classList.add('pulse');
    setTimeout(() => {
        button.classList.remove('pulse');
    }, 400);
}

// Carregar estatísticas
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        if (response.ok) {
            const stats = await response.json();
            Object.keys(stats).forEach(tipo => {
                updateCounter(tipo, stats[tipo]);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}
