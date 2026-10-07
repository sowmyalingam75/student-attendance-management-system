/**
 * Student Attendance Management System - Chart.js Initializations
 * Renders modern, responsive interactive charts for Admin and Student Dashboards
 */

document.addEventListener('DOMContentLoaded', () => {
    initAdminCharts();
    initStudentCharts();
});

/* -------------------------------------------------------------------------
   Admin Dashboard Charts
   ------------------------------------------------------------------------- */
function initAdminCharts() {
    // 1. Daily / Monthly Attendance Trend Chart
    const trendCtx = document.getElementById('attendanceTrendChart');
    if (trendCtx && window.trendLabels && window.trendPresent && window.trendAbsent) {
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: window.trendLabels,
                datasets: [
                    {
                        label: 'Present Count',
                        data: window.trendPresent,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Absent Count',
                        data: window.trendAbsent,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.08)',
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#ef4444',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: { family: "'Inter', sans-serif", weight: '600', size: 12 },
                            usePointStyle: true,
                            boxWidth: 8
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleFont: { family: "'Outfit', sans-serif", weight: 'bold' },
                        bodyFont: { family: "'Inter', sans-serif" },
                        padding: 10,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: "'Inter', sans-serif", size: 11 }, color: '#64748b' }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        ticks: { font: { family: "'Inter', sans-serif", size: 11 }, color: '#64748b', precision: 0 }
                    }
                }
            }
        });
    }

    // 2. Attendance Status Doughnut Chart (Present vs Absent)
    const donutCtx = document.getElementById('attendanceDonutChart');
    if (donutCtx && typeof window.todayPresent !== 'undefined' && typeof window.todayAbsent !== 'undefined') {
        const total = (window.todayPresent || 0) + (window.todayAbsent || 0);
        new Chart(donutCtx, {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent'],
                datasets: [{
                    data: total === 0 ? [1, 0] : [window.todayPresent, window.todayAbsent],
                    backgroundColor: total === 0 ? ['#e2e8f0', '#cbd5e1'] : ['#10b981', '#ef4444'],
                    hoverBackgroundColor: total === 0 ? ['#cbd5e1', '#94a3b8'] : ['#059669', '#dc2626'],
                    borderWidth: 3,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: { family: "'Inter', sans-serif", weight: '600', size: 12 },
                            usePointStyle: true,
                            boxWidth: 8
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        padding: 10,
                        cornerRadius: 8
                    }
                }
            }
        });
    }

    // 3. Subject-wise Attendance Percentage Bar Chart
    const subjectCtx = document.getElementById('subjectAttendanceChart');
    if (subjectCtx && window.subjectLabels && window.subjectPercentages) {
        new Chart(subjectCtx, {
            type: 'bar',
            data: {
                labels: window.subjectLabels,
                datasets: [{
                    label: 'Attendance %',
                    data: window.subjectPercentages,
                    backgroundColor: window.subjectPercentages.map(pct => 
                        pct >= 75 ? 'rgba(37, 99, 235, 0.85)' : (pct >= 65 ? 'rgba(245, 158, 11, 0.85)' : 'rgba(239, 68, 68, 0.85)')
                    ),
                    borderRadius: 6,
                    maxBarThickness: 38
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` Attendance: ${ctx.parsed.y}%`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: "'Inter', sans-serif", size: 11 }, color: '#64748b' }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            callback: (v) => v + '%',
                            font: { family: "'Inter', sans-serif", size: 11 },
                            color: '#64748b'
                        }
                    }
                }
            }
        });
    }
}

/* -------------------------------------------------------------------------
   Student Dashboard Charts
   ------------------------------------------------------------------------- */
function initStudentCharts() {
    const studentSubCtx = document.getElementById('studentSubjectChart');
    if (studentSubCtx && window.studentSubjects && window.studentPercentages) {
        new Chart(studentSubCtx, {
            type: 'bar',
            data: {
                labels: window.studentSubjects,
                datasets: [{
                    label: 'Attendance %',
                    data: window.studentPercentages,
                    backgroundColor: window.studentPercentages.map(pct =>
                        pct >= 75 ? '#10b981' : (pct >= 65 ? '#f59e0b' : '#ef4444')
                    ),
                    borderRadius: 6,
                    maxBarThickness: 42
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` Your Attendance: ${ctx.parsed.y}%`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: "'Inter', sans-serif", size: 11 }, color: '#64748b' }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            callback: (v) => v + '%',
                            font: { family: "'Inter', sans-serif", size: 11 },
                            color: '#64748b'
                        }
                    }
                }
            }
        });
    }
}
