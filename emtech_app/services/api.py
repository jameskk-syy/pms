import frappe
from frappe import auth

@frappe.whitelist( allow_guest=True )
def login(usr, pwd):
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Authentication Error!"
        }

        return

    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)

    frappe.response["message"] = {
        "success_key":1,
        "message":"Authentication success",
        "sid":frappe.session.sid,
        "api_key":user.api_key,
        "api_secret":api_generate,
        "username":user.username,
        "role": user.roles,
        "email":user.email
    }



def generate_keys(user):
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)

    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key

    user_details.api_secret = api_secret
    user_details.save()

    return api_secret


@frappe.whitelist(allow_guest=True)
def printName():
    return "Emtech App API"


@frappe.whitelist(allow_guest=True)
def logout():
    try:
        auth.logout()
        frappe.response["message"] = {
            "success_key": 1,
            "message": "Logged out successfully"
        }
    except Exception as e:
        frappe.response["message"] = {
            "success_key": 0,
            "message": f"Logout failed: {str(e)}"
        }


@frappe.whitelist(allow_guest=True)
def get_user_details():
    user = frappe.session.user
    user_details = frappe.get_doc('User', user)
    frappe.response["message"] = {
        "success_key": 1,
        "message": "User details retrieved successfully",
        "user_details": {
            "username": user_details.username,
            "email": user_details.email,
            "roles": [role.role for role in user_details.roles]
        }
    }



