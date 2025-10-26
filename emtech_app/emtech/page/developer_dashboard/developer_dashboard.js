frappe.pages['developer-dashboard'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Project Summary',
        single_column: true
    });

    // Set background color and reset layout
    $(page.body).css({
        'background-color': '#e6f0fa',
         'min-height': '80vh',
        'padding': '10px'
    }).html(`
        <div class="dashboard-layout" style="display: flex; gap: 20px;">
            <aside class="sidebar" style="width: 250px; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); height: fit-content;">
                <div class="link-group">
                    <h4>Projects</h4>
                    <a href="/app/project">Project</a>
                    <a href="/app/project-type">Project Type</a>
                    <a href="/app/project-update">Project Update</a>
                    <a href="/app/task">Task</a>
                </div>
                <div class="link-group">
                    <h4>Time Tracking</h4>
                    <a href="#">Activity Type</a>
                </div>
                <div class="link-group">
                    <h4>Reports</h4>
                    <a href="/app/query-report/Daily Timesheet Summary">Daily Timesheet Summary</a>
                    <a href="/app/query-report/Delayed Tasks Summary">Delayed Tasks Summary</a>
                    <a href="/app/query-report/Project Summary">Projects Summary Report</a>
                </div>
            </aside>
            <main class="dashboard-main" style="flex: 1;">
                <div id="dashboard-main-content"></div>
            </main>
        </div>
    `);

    // Add styles
    const styleTag = document.createElement('style');
    styleTag.innerHTML = `
        .card-box {
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            padding: 20px;
            margin: 10px;
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: white;
            min-width: 220px;
        }
        .card-icon {
            font-size: 2.2rem;
            margin-right: 15px;
        }
        .card-text {
            text-align: right;
        }
        .card-title {
            font-weight: 600;
            margin-bottom: 3px;
            font-size: 0.95rem;
        }
        .card-value {
            font-size: 1.6rem;
        }
        .row-flex {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        .chart-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            padding: 20px;
            margin: 10px;
            flex: 1;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .chart-container canvas {
            max-height: 500px !important;
            width: 100% !important;
        }
        .link-group h4 {
            margin-bottom: 15px;
            font-weight: 600;
        }
        .link-group a {
            display: block;
            margin-bottom: 10px;
            color: #1e3a8a;
            text-decoration: none;
        }
        .link-group a:hover {
            text-decoration: underline;
        }
        @media (max-width: 768px) {
            .dashboard-layout {
                flex-direction: column;
            }
            .sidebar {
                width: 100% !important;
            }
            .card-box, .chart-container {
                flex: 1 1 100% !important;
            }
        }
    `;
    document.head.appendChild(styleTag);

    // Font Awesome
    const faLink = document.createElement('link');
    faLink.rel = 'stylesheet';
    faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css';
    document.head.appendChild(faLink);

    // Main Content
    $('#dashboard-main-content').html(`
        <div class="row-flex" id="task-cards">
            <div class="card-box" style="background-color: #4dabf7;">
                <i class="fa-solid fa-layer-group card-icon"></i>
                <div class="card-text">
                    <div class="card-title">Total Tasks</div>
                    <div id="total_tasks" class="card-value">-</div>
                </div>
            </div>
            <div class="card-box" style="background-color: #43a047;">
                <i class="fa-solid fa-check-circle card-icon"></i>
                <div class="card-text">
                    <div class="card-title">Completed</div>
                    <div id="completed_tasks" class="card-value">-</div>
                </div>
            </div>
            <div class="card-box" style="background-color: #e53935;">
                <i class="fa-solid fa-exclamation-triangle card-icon"></i>
                <div class="card-text">
                    <div class="card-title">Overdue</div>
                    <div id="overdue_tasks" class="card-value">-</div>
                </div>
            </div>
            <div class="card-box" style="background-color: #1e3a8a;">
                <i class="fa-solid fa-spinner card-icon"></i>
                <div class="card-text">
                    <div class="card-title">Working</div>
                    <div id="working_tasks" class="card-value">-</div>
                </div>
            </div>
        </div>
        <div class="row-flex">
            <div class="chart-container"><canvas id="taskChart"></canvas></div>
            <div class="chart-container"><canvas id="pieChart"></canvas></div>
        </div>
    `);

    // Load Chart.js
    const chartJsSrc = "https://cdn.jsdelivr.net/npm/chart.js";
    const dataLabelPluginSrc = "https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels";
    function loadScript(url, callback) {
        const script = document.createElement('script');
        script.src = url;
        script.onload = callback;
        document.head.appendChild(script);
    }
    if (!window.Chart) {
        loadScript(chartJsSrc, () => loadScript(dataLabelPluginSrc, drawCharts));
    } else if (!Chart.plugins.getAll().some(p => p.id === 'datalabels')) {
        loadScript(dataLabelPluginSrc, drawCharts);
    } else {
        drawCharts();
    }

    function drawCharts() {
        frappe.call({
            method: 'emtech_app.services.dashboard.get_task_data',
            callback: function (r) {
                if (!r.message || r.message.length === 0) {
                    frappe.msgprint("No task data available");
                    return;
                }

                const data = r.message;
                const labels = data.map(item => item.project_name);
                const overdue = data.map(item => item.overdue);
                const working = data.map(item => item.working);
                const completed = data.map(item => item.completed);

                const totalTasks = overdue.reduce((a, b) => a + b, 0) +
                    working.reduce((a, b) => a + b, 0) +
                    completed.reduce((a, b) => a + b, 0);

                $('#total_tasks').text(totalTasks);
                $('#completed_tasks').text(completed.reduce((a, b) => a + b, 0));
                $('#overdue_tasks').text(overdue.reduce((a, b) => a + b, 0));
                $('#working_tasks').text(working.reduce((a, b) => a + b, 0));

                new Chart(document.getElementById('taskChart'), {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [
                            { label: 'Overdue', data: overdue, backgroundColor: '#e53935' },
                            { label: 'Working', data: working, backgroundColor: '#1e3a8a' },
                            { label: 'Completed', data: completed, backgroundColor: '#43a047' }
                        ]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: { display: true, text: 'Task Status by Project' }
                        },
                        scales: {
                            x: { stacked: true },
                            y: { stacked: true, beginAtZero: true }
                        }
                    }
                });

                new Chart(document.getElementById('pieChart'), {
                    type: 'pie',
                    data: {
                        labels: ['Overdue', 'Working', 'Completed'],
                        datasets: [{
                            data: [
                                overdue.reduce((a, b) => a + b, 0),
                                working.reduce((a, b) => a + b, 0),
                                completed.reduce((a, b) => a + b, 0)
                            ],
                            backgroundColor: ['#e53935', '#1e3a8a', '#43a047']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: { display: true, text: 'Overall Task Distribution' },
                            legend: { position: 'bottom' },
                            datalabels: {
                                formatter: (value, ctx) => {
                                    const total = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    return ((value / total * 100).toFixed(1)) + '%';
                                },
                                color: '#fff'
                            }
                        }
                    },
                    plugins: [ChartDataLabels]
                });
            }
        });
    }

    frappe.call({
        method: 'emtech_app.services.dashboard.get_my_dashboard_links',
        callback: function (r) {
            if (r.message) {
                if (r.message.task_url) {
                    $('.link-group a[href="/app/task"]').attr("href", r.message.task_url);
                }
                if (r.message.project_url) {
                    $('.link-group a[href="/app/project"]').attr("href", r.message.project_url);
                }
            }
        }
    });

    frappe.call({
        method: "emtech_app.services.dashboard.get_user_roles",
        callback: function (r) {
            if (!r.message) return;

            const roles = r.message;
            const hasRole = (role) => roles.includes(role);

            if (hasRole("Administrator")) return;

            if (hasRole("QA") || hasRole("deployment")) {
                const titlesToHide = ["Total Tasks", "Completed", "Overdue", "Working"];
                titlesToHide.forEach(title => {
                    $('#task-cards .card-box').filter(function () {
                        return $(this).find('.card-title').text().trim() === title;
                    }).hide();
                });

                $('.link-group:has(h4:contains("Projects")) a:contains("Project")').hide();
            }

            if (hasRole("QA") || hasRole("deployment") || hasRole("Developer")) {
                $('.link-group:has(h4:contains("Reports"))').hide();
            }

            if (hasRole("QA") || hasRole("deployment")) {
                frappe.call({
                    method: "emtech_app.services.dashboard.get_role_specific_task_data",
                    callback: function (res) {
                        if (!res.message) return;

                        const data = res.message;
                        let html = `
                            <div class="card-box" style="background-color: #6a1b9a;">
                                <i class="fa-solid fa-tasks card-icon"></i>
                                <div class="card-text">
                                    <div class="card-title">Total Assigned</div>
                                    <div class="card-value">${data.total_assigned}</div>
                                </div>
                            </div>
                            <div class="card-box" style="background-color: #00acc1;">
                                <i class="fa-solid fa-pen-nib card-icon"></i>
                                <div class="card-text">
                                    <div class="card-title">Signed</div>
                                    <div class="card-value">${data.signed}</div>
                                </div>
                            </div>
                        `;
                        if (hasRole("QA")) {
                            html += `
                                <div class="card-box" style="background-color: #2e7d32;">
                                    <i class="fa-solid fa-circle-check card-icon"></i>
                                    <div class="card-text">
                                        <div class="card-title">Passed</div>
                                        <div class="card-value">${data.passed}</div>
                                    </div>
                                </div>
                                <div class="card-box" style="background-color: #c62828;">
                                    <i class="fa-solid fa-circle-xmark card-icon"></i>
                                    <div class="card-text">
                                        <div class="card-title">Failed</div>
                                        <div class="card-value">${data.failed}</div>
                                    </div>
                                </div>
                            `;
                        }

                        if (hasRole("deployment")) {
                            html += `
                                <div class="card-box" style="background-color: #43a047;">
                                    <i class="fa-solid fa-cloud-upload-alt card-icon"></i>
                                    <div class="card-text">
                                        <div class="card-title">Deployed</div>
                                        <div class="card-value">${data.deployed}</div>
                                    </div>
                                </div>
                                <div class="card-box" style="background-color: #ff9800;">
                                    <i class="fa-solid fa-clock card-icon"></i>
                                    <div class="card-text">
                                        <div class="card-title">Pending</div>
                                        <div class="card-value">${data.pending}</div>
                                    </div>
                                </div>
                            `;
                        }

                        $("#task-cards").append(html);
                    }
                });
            }
        }
    });
};
