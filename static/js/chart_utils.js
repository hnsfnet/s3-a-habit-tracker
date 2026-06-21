const colorPalette = [
    '#10B981', '#3B82F6', '#F59E0B', '#8B5CF6',
    '#EF4444', '#06B6D4', '#F97316', '#EC4899',
    '#14B8A6', '#6366F1', '#84CC16', '#F43F5E',
];

const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

const chartInstances = {};

function destroyChart(canvasId) {
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
        chartInstances[canvasId] = null;
    }
}

function initWeeklyBarChart(canvasId, data, options = {}) {
    destroyChart(canvasId);

    const labels = [];
    const values = [];
    const sortedKeys = Object.keys(data).sort();
    sortedKeys.forEach((key) => {
        const d = new Date(key);
        labels.push(dayNames[d.getDay() === 0 ? 6 : d.getDay() - 1]);
        values.push(data[key]);
    });

    const ctx = document.getElementById(canvasId).getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: options.label || '完成习惯数',
                data: values,
                backgroundColor: options.backgroundColor || '#4F46E5',
                borderRadius: options.borderRadius || 6,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            },
            ...options.chartOptions
        }
    });

    return chartInstances[canvasId];
}

function initTrendBarChart(canvasId, data, options = {}) {
    destroyChart(canvasId);

    const labels = data.map(d => {
        const date = new Date(d.date);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    });
    const values = data.map(d => d.count);

    const ctx = document.getElementById(canvasId).getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: options.label || '每日完成数',
                data: values,
                backgroundColor: options.backgroundColor || 'rgba(79, 70, 229, 0.7)',
                borderColor: options.borderColor || '#4F46E5',
                borderWidth: options.borderWidth || 1,
                borderRadius: options.borderRadius || 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            },
            ...options.chartOptions
        }
    });

    return chartInstances[canvasId];
}

function initCategoryPieChart(canvasId, data, options = {}) {
    destroyChart(canvasId);

    if (data.length === 0) {
        return null;
    }

    const labels = data.map(d => d.category);
    const values = data.map(d => d.count);
    const colors = labels.map((_, i) => colorPalette[i % colorPalette.length]);

    const ctx = document.getElementById(canvasId).getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: options.borderColor || '#ffffff',
                borderWidth: options.borderWidth || 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 12 },
                        boxWidth: 10,
                    },
                    maxHeight: 120,
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const item = data[context.dataIndex];
                            return `${item.category}: ${item.count}次 (${item.percentage}%)`;
                        }
                    }
                }
            },
            ...options.chartOptions
        }
    });

    return chartInstances[canvasId];
}

function initMonthlyLineChart(canvasId, data, options = {}) {
    destroyChart(canvasId);

    const labels = data.map(d => d.month);
    const values = data.map(d => d.rate);

    const ctx = document.getElementById(canvasId).getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: options.label || '完成率 (%)',
                data: values,
                borderColor: options.borderColor || '#4F46E5',
                backgroundColor: options.backgroundColor || 'rgba(79, 70, 229, 0.1)',
                fill: true,
                tension: options.tension || 0.3,
                pointRadius: options.pointRadius || 5,
                pointHoverRadius: options.pointHoverRadius || 7,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            ...options.chartOptions
        }
    });

    return chartInstances[canvasId];
}
