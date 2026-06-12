class JarvisInterface {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.currentSection = 'dashboard';
        this.jarvisUrl = 'wss://jarvis-e4xu.onrender.com'; // TON URL RENDER
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.connectToJarvis();
        this.updateConnectionStatus();
        
        // Simuler des données système au début
        this.updateSystemMetrics({
            cpu_percent: 0,
            memory_percent: 0,
            disk_percent: 0
        });
        
        this.addLog('Interface JARVIS initialisée', 'system');
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });

        // Chat rapide
        const quickChatInput = document.getElementById('quickChatInput');
        const quickChatSend = document.getElementById('quickChatSend');
        
        quickChatSend.addEventListener('click', () => this.sendQuickMessage());
        quickChatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendQuickMessage();
        });

        // Chat complet
        const fullChatInput = document.getElementById('fullChatInput');
        const fullChatSend = document.getElementById('fullChatSend');
        
        fullChatSend.addEventListener('click', () => this.sendFullMessage());
        fullChatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendFullMessage();
        });

        // Widgets toggles
        document.querySelectorAll('.widget-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                const widget = e.target.closest('.widget');
                const content = widget.querySelector('.widget-content');
                const icon = e.target;
                
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
                icon.style.transform = content.style.display === 'none' ? 'rotate(180deg)' : 'rotate(0deg)';
            });
        });

        // Bouton paramètres
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.showSettings();
        });

        // Toggle thème
        document.getElementById('themeToggle').addEventListener('click', () => {
            this.toggleTheme();
        });
    }

    async connectToJarvis() {
        try {
            this.addLog('Tentative de connexion à JARVIS...', 'system');
            
            this.websocket = new WebSocket(`${this.jarvisUrl}/ws/interface/web-dashboard`);
            
            this.websocket.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus();
                this.addLog('✅ Connecté à JARVIS !', 'system');
                
                // Demander le statut des agents
                this.sendToJarvis('get_status', {});
            };

            this.websocket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleJarvisMessage(message);
            };

            this.websocket.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus();
                this.addLog('❌ Connexion à JARVIS fermée', 'system');
                
                // Tentative de reconnexion après 5 secondes
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connectToJarvis();
                    }
                }, 5000);
            };

            this.websocket.onerror = (error) => {
                this.addLog('❌ Erreur de connexion à JARVIS', 'system');
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            this.addLog('❌ Impossible de se connecter à JARVIS', 'system');
            console.error('Connection error:', error);
        }
    }

    sendToJarvis(type, data) {
        if (this.websocket && this.isConnected) {
            const message = {
                type: type,
                data: data,
                timestamp: new Date().toISOString(),
                source: 'web-interface'
            };
            this.websocket.send(JSON.stringify(message));
        }
    }

    handleJarvisMessage(message) {
        console.log('Message de JARVIS:', message);
        
        switch (message.type) {
            case 'welcome':
                this.addChatMessage('JARVIS', message.message, 'received');
                break;
                
            case 'status_response':
                this.updateAgentsStatus(message.data);
                break;
                
            case 'system_info':
                this.updateSystemMetrics(message.data);
                break;
                
            case 'chat_response':
                this.addChatMessage('JARVIS', message.data.response, 'received');
                break;
                
            case 'log':
                this.addLog(message.data.message, message.data.agent || 'jarvis');
                break;
                
            default:
                this.addLog(`Message reçu: ${message.type}`, 'jarvis');
        }
    }

    updateConnectionStatus() {
        const indicator = document.getElementById('connectionStatus');
        const icon = indicator.querySelector('i');
        
        if (this.isConnected) {
            indicator.className = 'status-indicator online';
            indicator.innerHTML = '<i class="fas fa-circle"></i> En ligne';
        } else {
            indicator.className = 'status-indicator offline';
            indicator.innerHTML = '<i class="fas fa-circle"></i> Hors ligne';
        }
    }

    updateSystemMetrics(data) {
        // CPU
        const cpuProgress = document.getElementById('cpuProgress');
        const cpuValue = document.getElementById('cpuValue');
        if (cpuProgress && cpuValue) {
            cpuProgress.style.width = `${data.cpu_percent || 0}%`;
            cpuValue.textContent = `${(data.cpu_percent || 0).toFixed(1)}%`;
        }

        // RAM
        const ramProgress = document.getElementById('ramProgress');
        const ramValue = document.getElementById('ramValue');
        if (ramProgress && ramValue) {
            ramProgress.style.width = `${data.memory_percent || 0}%`;
            ramValue.textContent = `${(data.memory_percent || 0).toFixed(1)}%`;
        }

        // Disque
        const diskProgress = document.getElementById('diskProgress');
        const diskValue = document.getElementById('diskValue');
        if (diskProgress && diskValue) {
            diskProgress.style.width = `${data.disk_percent || 0}%`;
            diskValue.textContent = `${(data.disk_percent || 0).toFixed(1)}%`;
        }
    }

    updateAgentsStatus(agents) {
        const agentsList = document.getElementById('agentsList');
        if (!agentsList) return;

        agentsList.innerHTML = '';
        
        if (agents && agents.length > 0) {
            agents.forEach(agentId => {
                const agentItem = document.createElement('div');
                agentItem.className = 'agent-item';
                agentItem.innerHTML = `
                    <div class="agent-info">
                        <span class="agent-name">${agentId}</span>
                        <span class="agent-type">Agent Local</span>
                    </div>
                    <div class="agent-status online">
                        <i class="fas fa-circle"></i> En ligne
                    </div>
                `;
                agentsList.appendChild(agentItem);
            });
        } else {
            agentsList.innerHTML = `
                <div class="agent-item">
                    <div class="agent-info">
                        <span class="agent-name">Aucun agent</span>
                        <span class="agent-type">En attente...</span>
                    </div>
                    <div class="agent-status offline">
                        <i class="fas fa-circle"></i> Hors ligne
                    </div>
                </div>
            `;
        }
    }

    sendQuickMessage() {
        const input = document.getElementById('quickChatInput');
        const message = input.value.trim();
        
        if (message && this.isConnected) {
            this.addChatMessage('Vous', message, 'sent');
            this.sendToJarvis('chat', { message: message });
            input.value = '';
        } else if (message) {
            this.addChatMessage('Système', 'Connexion à JARVIS requise', 'system');
        }
    }

    sendFullMessage() {
        const input = document.getElementById('fullChatInput');
        const message = input.value.trim();
        
        if (message && this.isConnected) {
            this.addFullChatMessage('Vous', message, 'sent');
            this.sendToJarvis('chat', { message: message });
            input.value = '';
        } else if (message) {
            this.addFullChatMessage('Système', 'Connexion à JARVIS requise', 'system');
        }
    }

    addChatMessage(sender, message, type) {
        const container = document.getElementById('quickChatMessages');
        this.appendMessage(container, sender, message, type);
    }

    addFullChatMessage(sender, message, type) {
        const container = document.getElementById('fullChatMessages');
        this.appendMessage(container, sender, message, type);
    }

    appendMessage(container, sender, message, type) {
        if (!container) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>${sender}</strong>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-content">${message}</div>
        `;
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }

    addLog(message, source = 'system') {
        const container = document.getElementById('recentLogs');
        if (!container) return;

        const logItem = document.createElement('div');
        logItem.className = 'log-item';
        logItem.innerHTML = `
            <span class="log-time">${new Date().toLocaleTimeString()}</span>
            <span class="log-message">[${source}] ${message}</span>
        `;
        
        container.appendChild(logItem);
        
        // Garder seulement les 10 derniers logs
        while (container.children.length > 10) {
            container.removeChild(container.firstChild);
        }
        
        container.scrollTop = container.scrollHeight;
    }

    switchSection(sectionName) {
        // Cacher toutes les sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Retirer l'état actif de tous les nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Afficher la section demandée
        const targetSection = document.getElementById(sectionName);
        const targetNavItem = document.querySelector(`[data-section="${sectionName}"]`);
        
        if (targetSection) targetSection.classList.add('active');
        if (targetNavItem) targetNavItem.classList.add('active');
        
        this.currentSection = sectionName;
        this.addLog(`Navigation vers ${sectionName}`, 'interface');
    }

    toggleTheme() {
        // Pour l'instant, on garde le thème sombre
        // Cette fonction sera étendue plus tard
        this.addLog('Basculement de thème (fonctionnalité à venir)', 'interface');
    }

    showSettings() {
        // Modal de paramètres (à implémenter plus tard)
        this.addLog('Ouverture des paramètres (à venir)', 'interface');
        alert('Paramètres - Fonctionnalité en développement');
    }
}

// Initialiser l'interface quand la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    window.jarvisInterface = new JarvisInterface();
});

// Styles CSS supplémentaires pour les messages
const additionalCSS = `
.chat-message {
    margin-bottom: 1rem;
    padding: 0.75rem;
    border-radius: 8px;
    max-width: 80%;
}

.chat-message.sent {
    background: var(--primary-color);
    color: var(--bg-primary);
    margin-left: auto;
}

.chat-message.received {
    background: var(--bg-tertiary);
    color: var(--text-primary);
}

.chat-message.system {
    background: var(--warning-color);
    color: var(--bg-primary);
    text-align: center;
    max-width: 100%;
}

.message-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.8rem;
    opacity: 0.8;
}

.message-content {
    line-height: 1.4;
}
`;

// Ajouter les styles CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalCSS;
document.head.appendChild(styleSheet);