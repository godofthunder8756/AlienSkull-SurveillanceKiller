/**
 * Timeline - Scan history visualization and management
 */

class Timeline {
    constructor(options = {}) {
        this.container = document.getElementById(options.containerId || 'timeline-container');
        this.api = options.api || new APIClient();
        this.scans = [];
        this.filters = {
            riskLevel: 'all',
            timeRange: 'all',
            searchQuery: ''
        };
    }

    async load(limit = 50) {
        try {
            const response = await this.api.getHistory(limit);
            this.scans = response.scans || [];
            this.render();
        } catch (error) {
            console.error('Failed to load timeline:', error);
            this.showError('Failed to load scan history');
        }
    }

    async loadScanDetails(scanId) {
        try {
            const response = await this.api.getScanDetail(scanId);
            return response.scan;
        } catch (error) {
            console.error('Failed to load scan details:', error);
            return null;
        }
    }

    setFilter(filterType, value) {
        this.filters[filterType] = value;
        this.render();
    }

    getFilteredScans() {
        return this.scans.filter(scan => {
            // Risk level filter
            if (this.filters.riskLevel !== 'all') {
                if (scan.threat_level !== this.filters.riskLevel) {
                    return false;
                }
            }

            // Search filter
            if (this.filters.searchQuery) {
                const query = this.filters.searchQuery.toLowerCase();
                // Search could be expanded to include SSID/MAC if we load full details
                if (!scan.timestamp.toLowerCase().includes(query)) {
                    return false;
                }
            }

            return true;
        });
    }

    render() {
        if (!this.container) return;

        const filteredScans = this.getFilteredScans();

        if (filteredScans.length === 0) {
            this.container.innerHTML = '<div class="timeline-empty">No scans found</div>';
            return;
        }

        this.container.innerHTML = filteredScans.map(scan => this.renderScanCard(scan)).join('');

        // Attach event listeners
        this.attachEventListeners();
    }

    renderScanCard(scan) {
        const timestamp = new Date(scan.timestamp);
        const timeString = timestamp.toLocaleString();
        const threatClass = `threat-${scan.threat_level}`;

        return `
            <div class="scan-card ${threatClass}" data-scan-id="${scan.id}">
                <div class="scan-header">
                    <div class="scan-time">${timeString}</div>
                    <div class="scan-threat">
                        <span class="threat-badge ${threatClass}">
                            ${scan.threat_level.toUpperCase()}
                        </span>
                    </div>
                </div>
                <div class="scan-stats">
                    <div class="scan-stat">
                        <span class="stat-icon">📡</span>
                        <span class="stat-text">${scan.wifi_count} Wi-Fi</span>
                    </div>
                    <div class="scan-stat">
                        <span class="stat-icon">📱</span>
                        <span class="stat-text">${scan.ble_count} BLE</span>
                    </div>
                    <div class="scan-stat risk-high">
                        <span class="stat-icon">⚠️</span>
                        <span class="stat-text">${scan.high_risk_count} High Risk</span>
                    </div>
                </div>
                <div class="scan-actions">
                    <button class="btn-secondary btn-view-details" data-scan-id="${scan.id}">
                        View Details
                    </button>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // View details buttons
        this.container.querySelectorAll('.btn-view-details').forEach(button => {
            button.addEventListener('click', async (e) => {
                const scanId = parseInt(e.target.dataset.scanId);
                await this.showScanDetails(scanId);
            });
        });
    }

    async showScanDetails(scanId) {
        const scan = await this.loadScanDetails(scanId);

        if (!scan) {
            alert('Failed to load scan details');
            return;
        }

        // Create modal/popup with details
        this.showDetailsModal(scan);
    }

    showDetailsModal(scan) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Scan Details</h2>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="scan-info">
                        <p><strong>Time:</strong> ${new Date(scan.timestamp).toLocaleString()}</p>
                        <p><strong>Threat Level:</strong>
                            <span class="threat-badge threat-${scan.threat_level}">
                                ${scan.threat_level.toUpperCase()}
                            </span>
                        </p>
                    </div>

                    <h3>Wi-Fi Networks (${scan.wifi.length})</h3>
                    <div class="networks-list">
                        ${scan.wifi.map(net => this.renderNetworkDetail(net)).join('')}
                    </div>

                    <h3>BLE Devices (${scan.ble.length})</h3>
                    <div class="devices-list">
                        ${scan.ble.map(dev => this.renderDeviceDetail(dev)).join('')}
                    </div>

                    ${scan.anomalies && scan.anomalies.length > 0 ? `
                        <h3>Anomalies Detected (${scan.anomalies.length})</h3>
                        <div class="anomalies-list">
                            ${scan.anomalies.map(a => this.renderAnomaly(a)).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close handlers
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    renderNetworkDetail(network) {
        const riskClass = `risk-${network.risk_level}`;
        const riskFactors = JSON.parse(network.risk_factors || '[]');

        return `
            <div class="network-detail ${riskClass}">
                <div class="network-header">
                    <span class="network-ssid">${network.ssid}</span>
                    <span class="risk-badge ${riskClass}">${network.risk_score}</span>
                </div>
                <div class="network-info">
                    <p><strong>BSSID:</strong> ${network.bssid}</p>
                    <p><strong>Security:</strong> ${network.security}</p>
                    <p><strong>Signal:</strong> ${network.rssi} dBm</p>
                    <p><strong>Channel:</strong> ${network.channel} (${network.frequency} MHz)</p>
                    <p><strong>Distance:</strong> ~${network.distance}m</p>
                </div>
                ${riskFactors.length > 0 ? `
                    <div class="risk-factors">
                        <strong>Risk Factors:</strong>
                        <ul>
                            ${riskFactors.map(f => `<li>${f}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderDeviceDetail(device) {
        const riskClass = `risk-${device.risk_level}`;
        const riskFactors = JSON.parse(device.risk_factors || '[]');

        return `
            <div class="device-detail ${riskClass}">
                <div class="device-header">
                    <span class="device-name">${device.name}</span>
                    <span class="risk-badge ${riskClass}">${device.risk_score}</span>
                </div>
                <div class="device-info">
                    <p><strong>MAC:</strong> ${device.mac}</p>
                    <p><strong>Type:</strong> ${device.device_type}</p>
                    <p><strong>Signal:</strong> ${device.rssi} dBm</p>
                    <p><strong>Distance:</strong> ~${device.distance}m</p>
                    ${device.is_tracker ? '<p class="warning">⚠️ Tracker Device</p>' : ''}
                </div>
                ${riskFactors.length > 0 ? `
                    <div class="risk-factors">
                        <strong>Risk Factors:</strong>
                        <ul>
                            ${riskFactors.map(f => `<li>${f}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderAnomaly(anomaly) {
        const severityClass = `severity-${anomaly.severity}`;

        return `
            <div class="anomaly-item ${severityClass}">
                <div class="anomaly-header">
                    <span class="anomaly-type">${anomaly.type.replace(/_/g, ' ').toUpperCase()}</span>
                    <span class="severity-badge ${severityClass}">${anomaly.severity}</span>
                </div>
                <p class="anomaly-description">${anomaly.description}</p>
            </div>
        `;
    }

    showError(message) {
        if (this.container) {
            this.container.innerHTML = `<div class="timeline-error">${message}</div>`;
        }
    }

    async exportData(format = 'json') {
        try {
            const response = await this.api.exportData(format, 7);

            if (format === 'json') {
                // Download JSON
                const blob = new Blob([JSON.stringify(response.data, null, 2)], {
                    type: 'application/json'
                });
                this.downloadBlob(blob, 'alienskull_export.json');
            } else if (format === 'csv') {
                // CSV is returned directly
                const blob = new Blob([response], {
                    type: 'text/csv'
                });
                this.downloadBlob(blob, 'alienskull_export.csv');
            }

        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to export data');
        }
    }

    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}
