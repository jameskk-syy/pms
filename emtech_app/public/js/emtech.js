frappe.router.render = function () {
    console.log("Router override active");
    const userRoles = frappe.boot.user.roles;
    console.log("Current User Roles:", userRoles);

    const isAdmin = userRoles.includes('Administrator');
    const project_user = userRoles.includes('Projects User');
    const project_manager = userRoles.includes('Projects Manager');


    console.log("Is Administrator?", isAdmin);

    if (this.current_route[0] === 'Workspaces' && this.current_route[1] === 'Home') {
        console.log("Redirecting from Workspaces > Home...");

        if (isAdmin || project_manager || project_user) {
            console.log("Redirecting to /app/developer-dashboard");
            frappe.set_route('developer-dashboard');
        } else if (userRoles.includes('Projects User')) {
            console.log("Redirecting to /app/developer-dashboard");
            frappe.set_route('developer-dashboard');
        } else {
            console.log("Redirecting to /app/task");
            frappe.set_route('task');
        }
        return;
    }

    if (this.current_route[0] === 'Workspaces' && this.current_route[1] === 'Projects') {
        if (isAdmin || project_manager || project_user) {
            console.log("Projects User detected on Projects workspace, redirecting to /app/task");
            frappe.set_route('developer-dashboard'); // redirect target
            console.log("After redirect, current route:", this.current_route);
            return;
        }
    }
    if (this.current_route[0] === 'Workspaces' && this.current_route[1] === 'Task') {
        if (isAdmin || project_manager || project_user) {
            console.log("Projects User detected on Projects workspace, redirecting to /app/task");
            frappe.set_route('developer-dashboard'); // redirect target
            console.log("After redirect, current route:", this.current_route);
            return;
        }
    }
    if (this.current_route[0]) {
        console.log("Rendering route:", this.current_route);
        this.render_page();
    } else {
        console.log("No route found, redirecting based on role");

        if (isAdmin) {
            frappe.set_route('developer-dashboard');
        } else {
            frappe.set_route('dashboard');
        }
    }
};
