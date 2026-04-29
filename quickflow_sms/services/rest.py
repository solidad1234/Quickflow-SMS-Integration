import frappe
import requests
import json

def get_api_credentials():
    settings = frappe.get_doc("Quickflow SMS Settings")
    if not settings.is_active:
        frappe.throw("Quickflow SMS Settings is not active.")
    
    if not settings.endpoint_url:
        frappe.throw("API Endpoint URL is missing in Quickflow SMS Settings.")
    
    api_key = settings.get_password("quickflow_api_key")
    api_secret = settings.get_password("quickflow_api_secret")
    
    if not api_key or not api_secret:
        frappe.throw("Quickflow API Key or Secret is missing in settings.")
        
    if not settings.sender_id:
        frappe.throw("Sender ID is missing in Quickflow SMS Settings.")
        
    return settings.endpoint_url, api_key, api_secret, settings.sender_id

def log_sms(status, message, recipients, error_log=None):
    log = frappe.get_doc({
        "doctype": "Quickflow SMS Log",
        "date": frappe.utils.now_datetime(),
        "status": status,
        "message": message,
        "recipients": recipients,
        "error_log": error_log
    })
    log.insert(ignore_permissions=True)
    frappe.db.commit()
    return log

@frappe.whitelist()
def send(recipients, message, type="plain", schedule_time=None, dlt_template_id=None):
    try:
        endpoint_url, api_key, api_secret, sender_id = get_api_credentials()
    except Exception as e:
        log_sms("Failed", message, recipients, str(e))
        return {"status": "error", "message": str(e)}

    base_url = endpoint_url.rstrip("/")
    url = f"{base_url}/api/method/quickflow.sms.send"

    headers = {
        "Authorization": f"Token {api_key}:{api_secret}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "recipient": recipients,
        "sender_id": sender_id,
        "type": type,
        "message": message
    }

    if schedule_time:
        payload["schedule_time"] = schedule_time
    if dlt_template_id:
        payload["dlt_template_id"] = dlt_template_id

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        # Support various standard frappe response formats
        status = "Success" if res_json.get("message", {}).get("status") == "success" or res_json.get("status") == "success" else "Failed"
        error_log = None if status == "Success" else json.dumps(res_json, indent=2)
        
        log_sms(status, message, recipients, error_log)
        return res_json
        
    except requests.exceptions.RequestException as e:
        frappe.log_error("Quickflow SMS Send Error", str(e))
        err_msg = str(e)
        log_sms("Failed", message, recipients, err_msg)
        return {"status": "error", "message": err_msg}

@frappe.whitelist()
def campaign(contact_list_id, message, type="plain", schedule_time=None, dlt_template_id=None):
    try:
        endpoint_url, api_key, api_secret, sender_id = get_api_credentials()
    except Exception as e:
        log_sms("Failed", message, f"Campaign Group: {contact_list_id}", str(e))
        return {"status": "error", "message": str(e)}

    base_url = endpoint_url.rstrip("/")
    url = f"{base_url}/api/method/quickflow.sms.campaign"

    headers = {
        "Authorization": f"Token {api_key}:{api_secret}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "contact_list_id": contact_list_id,
        "sender_id": sender_id,
        "type": type,
        "message": message
    }

    if schedule_time:
        payload["schedule_time"] = schedule_time
    if dlt_template_id:
        payload["dlt_template_id"] = dlt_template_id

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        status = "Success" if res_json.get("message", {}).get("status") == "success" or res_json.get("status") == "success" else "Failed"
        error_log = None if status == "Success" else json.dumps(res_json, indent=2)
        
        log_sms(status, message, f"Campaign Group: {contact_list_id}", error_log)
        return res_json
        
    except requests.exceptions.RequestException as e:
        frappe.log_error("Quickflow SMS Campaign Error", str(e))
        err_msg = str(e)
        log_sms("Failed", message, f"Campaign Group: {contact_list_id}", err_msg)
        return {"status": "error", "message": err_msg}

@frappe.whitelist()
def balance():
    try:
        endpoint_url, api_key, api_secret, sender_id = get_api_credentials()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    base_url = endpoint_url.rstrip("/")
    url = f"{base_url}/api/method/quickflow.sms.balance"

    headers = {
        "Authorization": f"Token {api_key}:{api_secret}",
        "Accept": "application/json"
    }

    params = {
        "sender_id": sender_id
    }

    try:
        # Many Frappe POST endpoints accept GET if not explicitly limited
        # But we can use POST just to be safe with frappe @frappe.whitelist() default behavior unless methods=["GET"] is specified.
        # Actually quickflow.sms.balance does not specify methods, so default allows POST and GET.
        response = requests.post(url, headers=headers, json=params, timeout=30)
        res_json = response.json()
        
        res_msg = res_json.get("message", {}) if isinstance(res_json.get("message"), dict) else res_json
        running_balance = res_msg.get("running_balance")
        
        if running_balance is not None:
            settings = frappe.get_doc("Quickflow SMS Settings")
            settings.db_set("balance", running_balance)
            
        return res_json
    except requests.exceptions.RequestException as e:
        frappe.log_error("Quickflow SMS Balance Error", str(e))
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def initiate_payment(amount, mobile):
    try:
        endpoint_url, api_key, api_secret, sender_id = get_api_credentials()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    base_url = endpoint_url.rstrip("/")
    url = f"{base_url}/api/method/quickflow.services.payment.initiate_payment"

    headers = {
        "Authorization": f"Token {api_key}:{api_secret}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "amount": amount,
        "mobile": mobile
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.json()
    except requests.exceptions.RequestException as e:
        frappe.log_error("Quickflow SMS Initiate Payment Error", str(e))
        return {"status": "error", "message": str(e)}
