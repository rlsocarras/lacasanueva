/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { Component, useState, onWillStart, useRef, onMounted } from "@odoo/owl";

export class FinanceBalanceDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.chartRef = useRef("chart");
        this.chartLineRef = useRef("chartLine");
        this.chart = null;
        this.chartLine = null;
        
        this.state = useState({
            filterType: 'month',
            year: new Date().getFullYear(),
            month: new Date().getMonth() + 1,
            quarter: Math.floor(new Date().getMonth() / 3) + 1,
            dateFrom: '',
            dateTo: '',
            specificDate: '',
            chartData: { sales: 0, purchases: 0, profit: 0 },
            lineData: { labels: [], sales: [], purchases: [] },
            loading: true,
            error: null,
            searchPanelCollapsed: false,
            activeReport: 'balance',
        });
        
        // ⭐ DEFINIR LOS MÉTODOS COMO FUNCIONES FLECHA EN setup()
        // Esto los expone automáticamente al template
        this.formatCurrency = (value) => {
            return (value || 0).toFixed(2);
        };
        
        this.formatAbsCurrency = (value) => {
            return Math.abs(value || 0).toFixed(2);
        };
        
        this.isProfit = () => {
            return (this.state.chartData.profit || 0) >= 0;
        };
        
        this.onFilterChange = async (ev) => {
            this.state.filterType = ev.target.value;
            await this.loadData();
        };
        
        this.onApplyFilter = async () => {
            await this.loadData();
        };

        this.setActiveReport = (reportId) => {
            if (this.state.activeReport !== reportId) {
                this.state.activeReport = reportId;
            }
        };

        this.toggleSearchPanel = () => {
            this.state.searchPanelCollapsed = !this.state.searchPanelCollapsed;
        };

        this.shareDashboard = async () => {
            const { dateFrom, dateTo } = this.getDateRange();
            const descripcion = `Balance de Compras y Ventas (${this.state.filterType}): ${dateFrom} → ${dateTo}`;
            try {
                if (navigator.clipboard) {
                    await navigator.clipboard.writeText(window.location.href);
                    this.notification.add("Enlace al reporte copiado al portapapeles", { type: "info" });
                } else {
                    this.notification.add(descripcion, { type: "info" });
                }
            } catch (error) {
                this.notification.add(descripcion, { type: "info" });
            }
        };
        
        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });
        
        onMounted(() => {
            this.renderChart();
        });
    }
    
    async loadData() {
        this.state.loading = true;
        this.state.error = null;
        
        try {
            const { dateFrom, dateTo } = this.getDateRange();
            
            const result = await this.orm.call(
                "finance.balance.analysis",
                "get_balance_data",
                [dateFrom, dateTo]
            );
            
            this.state.chartData = {
                sales: result.sales || 0,
                purchases: result.purchases || 0,
                profit: result.profit || 0,
            };

            this.state.lineData = {
                labels: result.labels || [],
                sales: result.sales_series || [],
                purchases: result.purchases_series || [],
            };
            
            setTimeout(() => this.renderChart(), 50);
            
        } catch (error) {
            console.error("Error al cargar datos:", error);
            this.state.error = error.message || "Error al cargar datos";
            this.state.chartData = { sales: 0, purchases: 0, profit: 0 };
            this.state.lineData = { labels: [], sales: [], purchases: [] };
        } finally {
            this.state.loading = false;
        }
    }
    
    getDateRange() {
        const s = this.state;
        const pad = n => String(n).padStart(2, '0');
        let from, to;
        
        if (s.filterType === 'year') {
            from = `${s.year}-01-01`;
            to = `${s.year}-12-31`;
        } else if (s.filterType === 'month') {
            from = `${s.year}-${pad(s.month)}-01`;
            const lastDay = new Date(s.year, s.month, 0).getDate();
            to = `${s.year}-${pad(s.month)}-${pad(lastDay)}`;
        } else if (s.filterType === 'quarter') {
            const startMonth = (s.quarter - 1) * 3 + 1;
            const endMonth = startMonth + 2;
            from = `${s.year}-${pad(startMonth)}-01`;
            const lastDay = new Date(s.year, endMonth, 0).getDate();
            to = `${s.year}-${pad(endMonth)}-${pad(lastDay)}`;
        } else if (s.filterType === 'range') {
            from = s.dateFrom || `${s.year}-01-01`;
            to = s.dateTo || `${s.year}-12-31`;
        } else if (s.filterType === 'specific') {
            from = s.specificDate || `${s.year}-01-01`;
            to = s.specificDate || `${s.year}-12-31`;
        }
        
        return { dateFrom: from, dateTo: to };
    }
    
    renderChart() {
        const canvas = this.chartRef.el;
        if (!canvas) return;
        
        if (typeof Chart === 'undefined') {
            console.warn("[LCN] Chart.js aún no está cargado");
            return;
        }
        
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        const ctx = canvas.getContext('2d');
        const data = this.state.chartData;
        
        const sales = data.sales || 0;
        const purchases = data.purchases || 0;
        const profit = data.profit || 0;
        
        const profitColor = profit >= 0 ? '#8fbf9f' : '#e0988f';
        const profitBorder = profit >= 0 ? '#6fa383' : '#c47870';

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Ventas', 'Compras', 'Ganancia/Pérdida'],
                datasets: [{
                    label: 'Monto',
                    data: [sales, purchases, profit],
                    backgroundColor: ['#7ba7cc', '#d18bb0', profitColor],
                    borderColor: ['#4f7da8', '#c25f92', profitBorder],
                    borderWidth: 1,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Balance Financiero',
                        font: { size: 16 }
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        this._renderLineChart();
    }

    _renderLineChart() {
        const canvas = this.chartLineRef.el;
        if (!canvas) return;

        if (typeof Chart === 'undefined') return;

        if (this.chartLine) {
            this.chartLine.destroy();
            this.chartLine = null;
        }

        const line = this.state.lineData;
        const labels = (line.labels || []).map(label => this.formatMonthLabel(label));
        const sales = line.sales || [];
        const purchases = line.purchases || [];

        const ctx = canvas.getContext('2d');

        // Degradado suave hacia abajo (efecto de sombra bajo la línea)
        const altura = canvas.height || 450;
        const gradientSales = ctx.createLinearGradient(0, 0, 0, altura);
        gradientSales.addColorStop(0, 'rgba(123, 167, 204, 0.55)');
        gradientSales.addColorStop(1, 'rgba(123, 167, 204, 0.05)');

        const gradientPurchases = ctx.createLinearGradient(0, 0, 0, altura);
        gradientPurchases.addColorStop(0, 'rgba(216, 127, 168, 0.55)');
        gradientPurchases.addColorStop(1, 'rgba(216, 127, 168, 0.05)');

        this.chartLine = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                {
                    label: 'Ventas',
                    data: sales,
                    borderColor: '#4f7da8',
                    backgroundColor: gradientSales,
                    tension: 0.2,
                    fill: true,
                    pointRadius: 3,
                },
                {
                    label: 'Compras',
                    data: purchases,
                    borderColor: '#c25f92',
                    backgroundColor: gradientPurchases,
                    tension: 0.2,
                    fill: true,
                    pointRadius: 3,
                },
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                    title: {
                        display: true,
                        text: 'Evolución mensual',
                        font: { size: 16 }
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    formatMonthLabel(label) {
        if (!label) return '';
        const meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
                       'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
        const partes = label.split('-');
        if (partes.length >= 2) {
            const mes = meses[parseInt(partes[1], 10) - 1] || partes[1];
            return `${mes} ${partes[0]}`;
        }
        return label;
    }
}

FinanceBalanceDashboard.template = "lacasanueva.FinanceBalanceDashboard";

registry.category("actions").add("lacasanueva.finance_balance", FinanceBalanceDashboard);