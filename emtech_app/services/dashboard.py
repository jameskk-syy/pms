import frappe
from frappe.utils import getdate, nowdate
from frappe import _

@frappe.whitelist()
def get_task_data():
    user = frappe.session.user
    department = frappe.db.get_value("User", user, "department")
    today = getdate(nowdate())

    print(f"[INFO] Logged in user: {user}")
    print(f"[INFO] User department: {department}")
    print(f"[INFO] Today's date: {today}")

    # Check for empty department or 'All'
    if not department or department.strip().lower() == "all - e":
        projects = frappe.get_all("Project", fields=["name", "project_name"])
    else:
        projects = frappe.get_all("Project", filters={"department": department}, fields=["name", "project_name"])

    print(f"[INFO] Found projects: {projects}")

    data = []

    for project in projects:
        tasks = frappe.get_all("Task", filters={"project": project.name}, fields=["status", "exp_end_date"])

        overdue = 0
        completed = 0
        working = 0

        for task in tasks:
            exp_end_date = getdate(task.exp_end_date) if task.exp_end_date else None
            if task.status == "Completed":
                completed += 1
            elif exp_end_date and exp_end_date < today:
                overdue += 1
            else:
                working += 1

        print(f"[DEBUG] Project: {project.project_name}, Overdue: {overdue}, Working: {working}, Completed: {completed}")

        data.append({
            "project_name": project.project_name,
            "overdue": overdue,
            "working": working,
            "completed": completed
        })

    return data


@frappe.whitelist()
def get_my_dashboard_links():
    from urllib.parse import quote

    user = frappe.session.user
    roles = frappe.get_roles(user)

    task_url = "/app/task"
    project_url = "/app/project"

    if "Administrator" in roles or "Project Manager" in roles:
        return {
            "task_url": task_url,
            "project_url": project_url
        }

    role_map = {
        "Developer": "custom_assign_developer",
        "QA": "custom_assign_qa_user",
        "deployment": "custom_assign_deployment_user"
    }

    user_email = frappe.db.get_value("User", user, "email")

    # Set task URL
    for role, param_key in role_map.items():
        if role in roles and user_email:
            task_url = f"/app/task/view/List?{param_key}={frappe.utils.cstr(user_email)}"
            break

    # Set project URL
    department = frappe.db.get_value("User", user, "department")

    if department:
        project_url = f"/app/project?department={quote(department)}"
    elif "QA" in roles or "deployment" in roles:
        # frappe.msgprint("No department set, checking latest assigned project...")

        task = frappe.get_all(
            "Task",
            filters=[],
            or_filters=[
                ["custom_assign_qa_user", "=", user_email],
                ["custom_assign_deployment_user", "=", user_email]
            ],
            fields=["project"],
            order_by="modified desc",
            limit=1
        )

        if task and task[0].get("project"):
            project_name = task[0]["project"]
            # frappe.msgprint(f"No department but has project: {project_name}")
            project_url = f"/app/project?status=open"
        else:
            pass
            # frappe.msgprint("No department and no recent project found")

    return {
        "task_url": task_url,
        "project_url": project_url
    }

@frappe.whitelist()
def get_user_roles():
    user = frappe.session.user
    roles = frappe.get_roles(user)
    return roles

@frappe.whitelist()
def get_role_specific_task_data():
    user = frappe.session.user
    roles = frappe.get_roles(user)
    email = frappe.db.get_value("User", user, "email")

    filters = {}
    if "QA" in roles:
        filters["custom_assign_qa_user"] = email
    elif "deployment" in roles:
        filters["custom_assign_deployment_user"] = email
    else:
        return {}

    tasks = frappe.get_all("Task", filters=filters, fields=["workflow_state", "custom_test_status"])

    total_assigned = len(tasks)
    signed = sum(1 for t in tasks if t.workflow_state == "signed")

    data = {"total_assigned": total_assigned, "signed": signed}

    if "QA" in roles:
        data["passed"] = sum(1 for t in tasks if t.custom_test_status == "Pass")
        data["failed"] = sum(1 for t in tasks if t.custom_test_status == "Fail")

    if "deployment" in roles:
        data["deployed"] = signed
        data["pending"] = total_assigned - signed

    return data





