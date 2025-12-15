/**
 * Radar Visualization - Tactical HUD with real-time network plotting
 */

class RadarDisplay {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        // Configuration
        this.maxDistance = options.maxDistance || 100; // meters
        this.rangeRings = [25, 50, 75, 100]; // meter intervals
        this.sweepAngle = 0;
        this.sweepSpeed = 2; // degrees per frame
        this.showSweep = options.showSweep !== false;

        // Data storage
        this.networks = [];
        this.devices = [];
        this.selectedItem = null;

        // Colors (tactical theme)
        this.colors = {
            background: '#000814',
            gridPrimary: '#003566',
            gridSecondary: '#001d3d',
            sweep: 'rgba(0, 245, 255, 0.2)',
            sweepLine: '#00f5ff',
            text: '#caf0f8',
            low: '#00f5ff',    // Cyan
            medium: '#ffba08', // Amber
            high: '#ff0054',   // Red
            ble: '#9d4edd'     // Purple
        };

        // Setup
        this.resize();
        this.setupEventListeners();

        // Start animation loop
        this.animate();
    }

    resize() {
        // Make canvas fill container
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;

        // Calculate center and scale
        this.centerX = this.canvas.width / 2;
        this.centerY = this.canvas.height / 2;
        this.radius = Math.min(this.centerX, this.centerY) - 40;
        this.scale = this.radius / this.maxDistance;
    }

    setupEventListeners() {
        // Resize handling
        window.addEventListener('resize', () => {
            this.resize();
            this.draw();
        });

        // Click handling for details
        this.canvas.addEventListener('click', (e) => {
            this.handleClick(e);
        });

        // Hover handling
        this.canvas.addEventListener('mousemove', (e) => {
            this.handleHover(e);
        });
    }

    animate() {
        // Update sweep angle
        if (this.showSweep) {
            this.sweepAngle = (this.sweepAngle + this.sweepSpeed) % 360;
        }

        // Redraw
        this.draw();

        // Continue animation
        requestAnimationFrame(() => this.animate());
    }

    draw() {
        // Clear canvas
        this.ctx.fillStyle = this.colors.background;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw components
        this.drawGrid();
        this.drawRangeRings();
        this.drawCardinalDirections();
        this.drawSweep();
        this.drawNetworks();
        this.drawDevices();
        this.drawCenterMarker();
        this.drawLegend();
    }

    drawGrid() {
        this.ctx.strokeStyle = this.colors.gridSecondary;
        this.ctx.lineWidth = 0.5;

        // Radial lines (every 30 degrees)
        for (let angle = 0; angle < 360; angle += 30) {
            const rad = angle * Math.PI / 180;
            const x = this.centerX + this.radius * Math.cos(rad - Math.PI / 2);
            const y = this.centerY + this.radius * Math.sin(rad - Math.PI / 2);

            this.ctx.beginPath();
            this.ctx.moveTo(this.centerX, this.centerY);
            this.ctx.lineTo(x, y);
            this.ctx.stroke();
        }
    }

    drawRangeRings() {
        this.rangeRings.forEach((range, index) => {
            const r = range * this.scale;

            // Ring
            this.ctx.strokeStyle = this.colors.gridPrimary;
            this.ctx.lineWidth = index === this.rangeRings.length - 1 ? 2 : 1;
            this.ctx.beginPath();
            this.ctx.arc(this.centerX, this.centerY, r, 0, Math.PI * 2);
            this.ctx.stroke();

            // Label
            this.ctx.fillStyle = this.colors.text;
            this.ctx.font = '12px monospace';
            this.ctx.fillText(`${range}m`, this.centerX + 5, this.centerY - r + 15);
        });
    }

    drawCardinalDirections() {
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = 'bold 16px monospace';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';

        const offset = this.radius + 25;

        // N, E, S, W
        this.ctx.fillText('N', this.centerX, this.centerY - offset);
        this.ctx.fillText('E', this.centerX + offset, this.centerY);
        this.ctx.fillText('S', this.centerX, this.centerY + offset);
        this.ctx.fillText('W', this.centerX - offset, this.centerY);
    }

    drawSweep() {
        if (!this.showSweep) return;

        const rad = this.sweepAngle * Math.PI / 180;

        // Sweep gradient
        const gradient = this.ctx.createRadialGradient(
            this.centerX, this.centerY, 0,
            this.centerX, this.centerY, this.radius
        );
        gradient.addColorStop(0, this.colors.sweep);
        gradient.addColorStop(1, 'rgba(0, 245, 255, 0)');

        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.moveTo(this.centerX, this.centerY);
        this.ctx.arc(
            this.centerX, this.centerY, this.radius,
            rad - Math.PI / 2 - Math.PI / 6,
            rad - Math.PI / 2,
            false
        );
        this.ctx.closePath();
        this.ctx.fill();

        // Sweep line
        this.ctx.strokeStyle = this.colors.sweepLine;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(this.centerX, this.centerY);
        this.ctx.lineTo(
            this.centerX + this.radius * Math.cos(rad - Math.PI / 2),
            this.centerY + this.radius * Math.sin(rad - Math.PI / 2)
        );
        this.ctx.stroke();
    }

    drawNetworks() {
        this.networks.forEach(network => {
            this.drawContact(
                network.position.x,
                network.position.y,
                network.color,
                network.ssid || '<hidden>',
                network === this.selectedItem
            );
        });
    }

    drawDevices() {
        this.devices.forEach(device => {
            this.drawContact(
                device.position.x,
                device.position.y,
                this.colors.ble,
                device.name || '<unnamed>',
                device === this.selectedItem,
                true // is BLE
            );
        });
    }

    drawContact(x, y, color, label, selected = false, isBLE = false) {
        // Convert position to canvas coordinates
        const canvasX = this.centerX + x * this.scale;
        const canvasY = this.centerY + y * this.scale;

        // Check if within display radius
        const distance = Math.sqrt(x * x + y * y);
        if (distance > this.maxDistance) return;

        // Draw marker
        this.ctx.fillStyle = color;
        this.ctx.strokeStyle = selected ? '#ffffff' : color;
        this.ctx.lineWidth = selected ? 2 : 1;

        if (isBLE) {
            // Triangle for BLE devices
            this.ctx.beginPath();
            this.ctx.moveTo(canvasX, canvasY - 6);
            this.ctx.lineTo(canvasX + 5, canvasY + 4);
            this.ctx.lineTo(canvasX - 5, canvasY + 4);
            this.ctx.closePath();
            this.ctx.fill();
            this.ctx.stroke();
        } else {
            // Circle for Wi-Fi networks
            this.ctx.beginPath();
            this.ctx.arc(canvasX, canvasY, selected ? 6 : 4, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.stroke();
        }

        // Draw label if selected or zoomed in
        if (selected || distance < 30) {
            this.ctx.fillStyle = this.colors.text;
            this.ctx.font = '11px monospace';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(label, canvasX, canvasY - 12);
        }

        // Pulse effect for high risk
        if (color === this.colors.high) {
            const pulseRadius = 8 + Math.sin(Date.now() / 200) * 2;
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 1;
            this.ctx.globalAlpha = 0.3;
            this.ctx.beginPath();
            this.ctx.arc(canvasX, canvasY, pulseRadius, 0, Math.PI * 2);
            this.ctx.stroke();
            this.ctx.globalAlpha = 1.0;
        }
    }

    drawCenterMarker() {
        // Device position indicator
        this.ctx.strokeStyle = this.colors.low;
        this.ctx.lineWidth = 2;

        // Crosshair
        this.ctx.beginPath();
        this.ctx.moveTo(this.centerX - 10, this.centerY);
        this.ctx.lineTo(this.centerX + 10, this.centerY);
        this.ctx.moveTo(this.centerX, this.centerY - 10);
        this.ctx.lineTo(this.centerX, this.centerY + 10);
        this.ctx.stroke();

        // Circle
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, 15, 0, Math.PI * 2);
        this.ctx.stroke();

        // Label
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = '12px monospace';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('YOU', this.centerX, this.centerY + 30);
    }

    drawLegend() {
        const x = 20;
        const y = this.canvas.height - 120;

        this.ctx.font = '12px monospace';
        this.ctx.textAlign = 'left';

        // Legend items
        const items = [
            { color: this.colors.low, label: 'Low Risk' },
            { color: this.colors.medium, label: 'Medium Risk' },
            { color: this.colors.high, label: 'High Risk' },
            { color: this.colors.ble, label: 'BLE Device' }
        ];

        items.forEach((item, i) => {
            // Color box
            this.ctx.fillStyle = item.color;
            this.ctx.fillRect(x, y + i * 25, 15, 15);

            // Label
            this.ctx.fillStyle = this.colors.text;
            this.ctx.fillText(item.label, x + 25, y + i * 25 + 11);
        });
    }

    handleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;

        // Check networks
        for (let network of this.networks) {
            const canvasX = this.centerX + network.position.x * this.scale;
            const canvasY = this.centerY + network.position.y * this.scale;
            const distance = Math.sqrt(
                Math.pow(clickX - canvasX, 2) + Math.pow(clickY - canvasY, 2)
            );

            if (distance < 10) {
                this.selectedItem = network;
                this.onItemSelected(network, 'wifi');
                return;
            }
        }

        // Check devices
        for (let device of this.devices) {
            const canvasX = this.centerX + device.position.x * this.scale;
            const canvasY = this.centerY + device.position.y * this.scale;
            const distance = Math.sqrt(
                Math.pow(clickX - canvasX, 2) + Math.pow(clickY - canvasY, 2)
            );

            if (distance < 10) {
                this.selectedItem = device;
                this.onItemSelected(device, 'ble');
                return;
            }
        }

        // Clear selection
        this.selectedItem = null;
        this.onItemSelected(null, null);
    }

    handleHover(e) {
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        let hovering = false;

        // Check if hovering over any contact
        [...this.networks, ...this.devices].forEach(item => {
            const canvasX = this.centerX + item.position.x * this.scale;
            const canvasY = this.centerY + item.position.y * this.scale;
            const distance = Math.sqrt(
                Math.pow(mouseX - canvasX, 2) + Math.pow(mouseY - canvasY, 2)
            );

            if (distance < 10) {
                hovering = true;
            }
        });

        this.canvas.style.cursor = hovering ? 'pointer' : 'default';
    }

    updateData(scanData) {
        this.networks = scanData.wifi || [];
        this.devices = scanData.ble || [];
    }

    toggleSweep() {
        this.showSweep = !this.showSweep;
    }

    // Override this method to handle selection events
    onItemSelected(item, type) {
        // To be implemented by user
        console.log('Selected:', type, item);
    }
}
