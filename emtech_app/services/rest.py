import frappe
from frappe.utils import nowdate, getdate
from frappe.utils.response import redirect
from frappe.utils.jinja import render_template



@frappe.whitelist()
def send_overdue_task_emails():
    logger = frappe.logger("Overdue Task Mailer")
    logger.info("Starting overdue task email job...")

    site_url = frappe.utils.get_url()
    today = getdate(nowdate())  # Convert to date object

    logger.info(f"Site URL: {site_url}")
    logger.info(f"Today's Date: {today}")
    

    # Fetch tasks
    all_tasks = frappe.get_all(
        "Task",
        fields=["name", "subject", "exp_end_date", "exp_start_date", "custom_assign_developer", "status", "priority"]
    )

    logger.info(f"Total tasks found: {len(all_tasks)}")

    for task in all_tasks:
        logger.info(f"Checking task: {task.name}, Subject: {task.subject}")

        try:
            # Skip if no end date or no assigned developer
            if not task.exp_end_date or not task.custom_assign_developer:
                logger.info(f"Skipping task {task.name} due to missing end date or assignee")
                continue

            end_date = getdate(task.exp_end_date)
            logger.info(f"Task {task.name} has end date: {end_date}")

            # Skip if not overdue
            if end_date >= today or task.status == "Completed" or task.status == "Cancelled":
                logger.info(f"Task {task.name} is not overdue (End Date: {end_date})")
                continue

            user_email = task.custom_assign_developer
            full_name = frappe.db.get_value("User", user_email, "full_name") or user_email
            task_name = task.name
            priority = task.priority
            due_date = task.exp_end_date
            task_url = f"{site_url}/app/task/{task.name}"
            subject = f"Overdue Task: {task.subject}"
            message ="hello  world"
            print("saved  successfully")
            if(task.status != "Overdue"):
                frappe.db.set_value('Task', task.name, 'status', 'Overdue')
                frappe.db.commit() 
            logger.info(f"Sending email to {user_email} for task {task.name}")
            frappe.log_error(f"Sending email to {user_email} for task {task.name}", "Task Assignment overdue Mailer")
            # frappe.sendmail(
            # recipients=[user_email],
            # subject=subject,
            # message=message
            # )en
            print("sent")
            send_task_assignment_overdue_email(task_url, user_email, task_name, subject,priority,due_date)
            logger.info(f"Email sent to {user_email} for task {task.name}")

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Error sending email for task {task.name}")
            logger.error(f"Error while processing task {task.name}: {str(e)}")

    logger.info("Finished overdue task email job.")


@frappe.whitelist()
def on_task_submit(doc, method):
    user_email = doc.custom_assign_developer
    task_name = doc.name
    priority = doc.priority
    due_date = doc.exp_end_date
    qa = doc.custom_assign_qa_user
    deployment = doc.custom_assign_deployment_user
    subject = doc.subject
    print(user_email)

    full_name = frappe.db.get_value("User", user_email, "full_name") or user_email
    site_url = frappe.utils.get_url()
    workflow_state = doc.workflow_state

    if workflow_state == "Pending Developer Completion":
        task_url = f"{site_url}/app/task/{task_name}"
        print(task_url)
        subject_line = f"New Task: {subject}"
        send_task_assignment_email(task_url, user_email, task_name, subject_line, priority, due_date)

    elif workflow_state == "Pending Qa Testing":
        task_url = f"{site_url}/app/task/{task_name}"
        print(task_url)
        subject_line = f"You have a new testing  task : {subject}"
        send_task_assignment_email(task_url, qa, task_name, subject_line, priority, due_date)

    elif workflow_state == "Pending Developer Recompletion":
        task_url = f"{site_url}/app/task/{task_name}"
        print(task_url)
        subject_line = f"Correction Task: {subject}"
        send_task_assignment_email(task_url, user_email, task_name, subject_line, priority, due_date)

    elif workflow_state == "Pending Program Manager Approval":
        pm_users = frappe.get_all("Has Role", filters={"role": "Program Manager"}, fields=["parent"])
        for user in pm_users:
            user_email = user.parent
            user_doc = frappe.get_doc("User", user_email)
            full_name = user_doc.full_name
            task_url = f"{site_url}/app/task/{task_name}"
            subject_line = f"Task Awaiting PM Approval: {subject}"
            send_task_assignment_email(task_url, user_email, task_name, subject_line, priority, due_date)

    elif workflow_state == "Pending Qa Restesting":
        task_url = f"{site_url}/app/task/{task_name}"
        print(task_url)
        subject_line = f"New Task for retesting: {subject}"
        send_task_assignment_email(task_url, qa, task_name, subject_line, priority, due_date)

    elif workflow_state == "Pending Deployment":
        task_url = f"{site_url}/app/task/{task_name}"
        print(task_url)
        subject_line = f"New Task for deployment: {subject}"
        send_task_assignment_email(task_url, deployment, task_name, subject_line, priority, due_date)

    elif workflow_state == "Deployed":
        pm_users = frappe.get_all("Has Role", filters={"role": "Program Manager"}, fields=["parent"])
        for user in pm_users:
            user_email = user.parent
            user_doc = frappe.get_doc("User", user_email)
            full_name = user_doc.full_name
            task_url = f"{site_url}/app/task/{task_name}"
            subject_line = f"Task Awaiting PM request for sign off: {subject}"
            send_task_assignment_email(task_url, user_email, task_name, subject_line, priority, due_date)

    elif workflow_state == "pending sign off":
        task_url = f"{site_url}/app/task/{task_name}"
        message =  doc.custom_program__manager_message_for__sign_off
        time_for_sign_off = doc.custom_date__time__for__sign_off
        subject_line = f"Task Pending Sign-Off: {subject} at {time_for_sign_off}" 
        

        # Send to all Project Managers
        pm_users = frappe.get_all("Has Role", filters={"role": "Program Manager"}, fields=["parent"])
        for user in pm_users:
            user_email_pm = user.parent
            user_doc = frappe.get_doc("User", user_email_pm)
            full_name = user_doc.full_name
            send_task_assignment_email(task_url, user_email_pm, task_name, subject_line, priority, due_date)

        # Send to specific users directly from the Task doc
        for assignee in [user_email, qa, deployment]:
            if assignee:
                user_doc = frappe.get_doc("User", assignee)
                full_name = user_doc.full_name
                send_task_assignment_email(task_url, assignee, task_name, subject_line, priority, due_date)

    elif workflow_state == "signed":
        task_url = f"{site_url}/app/task/{task_name}"
        subject_line = f"Task has  been  Signed-Off: {subject}"

        # Send to all Project Managers
        pm_users = frappe.get_all("Has Role", filters={"role": "Program Manager"}, fields=["parent"])
        for user in pm_users:
            user_email_pm = user.parent
            user_doc = frappe.get_doc("User", user_email_pm)
            full_name = user_doc.full_name
            send_task_assignment_email(task_url, user_email_pm, task_name, subject_line, priority, due_date)

        # Send to specific users directly from the Task doc
        for assignee in [user_email, qa, deployment]:
            if assignee:
                user_doc = frappe.get_doc("User", assignee)
                full_name = user_doc.full_name
                send_task_assignment_email(task_url, assignee, task_name, subject_line, priority, due_date)

@frappe.whitelist()
def send_task_assignment_email(task_url, user_email, task_name, subject,priority,due_date):
    full_name = frappe.db.get_value("User", user_email, "full_name") or user_email
    company_name = frappe.defaults.get_global_default("company") or "Your Company"
    local_image_url = "https://www.python.org/static/community_logos/python-logo.png"


    context = {
        "full_name": full_name,
        "subject": subject,
        "title": task_name,
        "priority": priority,
        "local_image_url": local_image_url,
        "due_date": due_date,
        "task_url": task_url,
        "company_name": company_name,
    }

    message = render_template("emtech_app/templates/emails/send_tasks.html", context)

    frappe.sendmail(
        recipients=[user_email],
        subject=subject,
        message=message
    )
    frappe.msgprint(f"Task  has  been emailed to {full_name}")
    frappe.log_error(f"Sent task assignment email to {user_email} for task {task_name}", "Task Assignment Mailer")


@frappe.whitelist()
def send_task_assignment_overdue_email(task_url, user_email, task_name, subject,priority,due_date):
    full_name = frappe.db.get_value("User", user_email, "full_name") or user_email
    company_name = frappe.defaults.get_global_default("company") or "Your Company"
    local_image_url = "https://www.python.org/static/community_logos/python-logo.png"


    context = {
        "full_name": full_name,
        "subject": subject,
        "title": task_name,
        "priority": priority,
        "local_image_url": local_image_url,
        "due_date": due_date,
        "task_url": task_url,
        "company_name": company_name,
    }

    message = render_template("emtech_app/templates/emails/overdue_tasks.html", context)

    frappe.sendmail(
        recipients=[user_email],
        subject=subject,
        message=message
    )
    frappe.msgprint(f"Task  has  been emailed to {full_name}")
    frappe.log_error(f"Sent task assignment email to {user_email} for task {task_name}", "Task Assignment Mailer")



@frappe.whitelist()
def get_users_by_roles():
    # frappe.msgprint("me ")
    def get_users(role):
        users = frappe.get_all("Has Role", filters={"role": role}, fields=["parent"])
        return [u.parent for u in users] or ["NA"]

    return {
        "QA": get_users("QA"),
        "Deployment": get_users("Deployment"),
        "Developer": get_users("Developer")
    }


@frappe.whitelist()
def get_listview_access_control():
    user = frappe.session.user
    roles = frappe.get_roles(user)

    # Always allow Administrator
    if "Administrator" in roles:
        return {
            "disable_click": False
        }

    restricted_roles = ["QA", "Developer", "Deployment"]

    # If any restricted role is found
    if any(role in roles for role in restricted_roles):
        return {
            "disable_click": True
        }

    # Default case
    return {
        "disable_click": False
    }

@frappe.whitelist()
def printMessage():
    return "hello  world"





