/**
 * WebSocket Client - Real-time communication with Flask-SocketIO
 */

class WebSocketClient {
    constructor(options = {}) {
        this.url = options.url || window.location.origin;
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.reconnectDelay = options.reconnectDelay || 2000;

        // Callbacks
        this.onConnected = options.onConnected || (() => {});
        this.onDisconnected = options.onDisconnected || (() => {});
        this.onScanUpdate = options.onScanUpdate || (() => {});
        this.onError = options.onError || (() => {});

        // Connect
        this.connect();
    }

    connect() {
        try {
            console.log('Connecting to WebSocket server...');

            // Initialize Socket.IO client
            this.socket = io(this.url, {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: this.reconnectDelay,
                reconnectionAttempts: this.maxReconnectAttempts
            });

            // Setup event handlers
            this.setupEventHandlers();

        } catch (error) {
            console.error('Failed to connect:', error);
            this.onError(error);
            this.scheduleReconnect();
        }
    }

    setupEventHandlers() {
        // Connection established
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.onConnected();
        });

        // Connection lost
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.connected = false;
            this.onDisconnected(reason);

            // Attempt reconnection if not intentional
            if (reason === 'io server disconnect') {
                this.socket.connect();
            }
        });

        // Connection error
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.onError(error);
        });

        // Reconnection attempt
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Reconnection attempt ${attemptNumber}...`);
            this.reconnectAttempts = attemptNumber;
        });

        // Reconnection success
        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`Reconnected after ${attemptNumber} attempts`);
            this.connected = true;
            this.reconnectAttempts = 0;
            this.onConnected();
        });

        // Reconnection failed
        this.socket.on('reconnect_failed', () => {
            console.error('Reconnection failed');
            this.onError(new Error('Failed to reconnect'));
        });

        // Scan update event
        this.socket.on('scan_update', (data) => {
            console.log('Received scan update:', data);
            this.onScanUpdate(data);
        });

        // Error event
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.onError(error);
        });

        // Connected acknowledgement
        this.socket.on('connected', (data) => {
            console.log('Server acknowledged connection:', data);
        });
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                console.log(`Reconnecting (attempt ${this.reconnectAttempts})...`);
                this.connect();
            }, this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
            this.onError(new Error('Failed to connect after maximum attempts'));
        }
    }

    requestScan() {
        if (this.connected) {
            console.log('Requesting scan...');
            this.socket.emit('request_scan');
        } else {
            console.warn('Cannot request scan: not connected');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.connected = false;
        }
    }

    isConnected() {
        return this.connected;
    }
}


/**
 * API Client - REST API communication
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL || window.location.origin;
    }

    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Request failed');
            }

            return data;

        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Scanning control
    async startScanning() {
        return this.post('/api/scan/start');
    }

    async stopScanning() {
        return this.post('/api/scan/stop');
    }

    async scanOnce() {
        return this.post('/api/scan/once');
    }

    // Configuration
    async getConfig() {
        return this.get('/api/config');
    }

    async updateConfig(config) {
        return this.post('/api/config', config);
    }

    // Status
    async getStatus() {
        return this.get('/api/status');
    }

    // History
    async getHistory(limit = 50) {
        return this.get(`/api/history?limit=${limit}`);
    }

    async getScanDetail(scanId) {
        return this.get(`/api/history/${scanId}`);
    }

    // Export
    async exportData(format = 'json', days = 7) {
        return this.get(`/api/export?format=${format}&days=${days}`);
    }

    // Cleanup
    async cleanupDatabase(days = 30) {
        return this.post('/api/cleanup', { days });
    }
}


/**
 * Status Manager - UI status indicator
 */

class StatusManager {
    constructor(elementId) {
        this.element = document.getElementById(elementId);
        this.status = 'disconnected';
    }

    setConnected() {
        this.status = 'connected';
        this.update('Connected', 'success');
    }

    setDisconnected() {
        this.status = 'disconnected';
        this.update('Disconnected', 'error');
    }

    setScanning() {
        this.status = 'scanning';
        this.update('Scanning...', 'scanning');
    }

    setIdle() {
        this.status = 'idle';
        this.update('Ready', 'success');
    }

    setError(message) {
        this.status = 'error';
        this.update(message, 'error');
    }

    update(text, type) {
        if (!this.element) return;

        this.element.textContent = text;
        this.element.className = `status status-${type}`;
    }

    getStatus() {
        return this.status;
    }
}


/**
 * Statistics Display - Show scan statistics
 */

class StatsDisplay {
    constructor(elementId) {
        this.element = document.getElementById(elementId);
    }

    update(stats) {
        if (!this.element || !stats) return;

        const wifi = stats.wifi || {};
        const ble = stats.ble || {};
        const threatLevel = stats.overall_threat_level || 'low';

        this.element.innerHTML = `
            <div class="stat-group">
                <h3>Wi-Fi Networks</h3>
                <div class="stat-item">
                    <span class="stat-label">Total:</span>
                    <span class="stat-value">${wifi.total || 0}</span>
                </div>
                <div class="stat-item risk-high">
                    <span class="stat-label">High Risk:</span>
                    <span class="stat-value">${wifi.by_risk?.high || 0}</span>
                </div>
                <div class="stat-item risk-medium">
                    <span class="stat-label">Medium Risk:</span>
                    <span class="stat-value">${wifi.by_risk?.medium || 0}</span>
                </div>
                <div class="stat-item risk-low">
                    <span class="stat-label">Low Risk:</span>
                    <span class="stat-value">${wifi.by_risk?.low || 0}</span>
                </div>
            </div>

            <div class="stat-group">
                <h3>BLE Devices</h3>
                <div class="stat-item">
                    <span class="stat-label">Total:</span>
                    <span class="stat-value">${ble.total || 0}</span>
                </div>
                <div class="stat-item risk-high">
                    <span class="stat-label">Trackers:</span>
                    <span class="stat-value">${ble.trackers || 0}</span>
                </div>
                <div class="stat-item risk-high">
                    <span class="stat-label">High Risk:</span>
                    <span class="stat-value">${ble.by_risk?.high || 0}</span>
                </div>
            </div>

            <div class="stat-group">
                <h3>Threat Level</h3>
                <div class="threat-level threat-${threatLevel}">
                    ${threatLevel.toUpperCase()}
                </div>
            </div>
        `;
    }

    clear() {
        if (this.element) {
            this.element.innerHTML = '<div class="stat-empty">No data</div>';
        }
    }
}
