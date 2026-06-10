import json
from urllib import error, request

from django.conf import settings


class MyFatoorahConfigurationError(Exception):
    pass


class MyFatoorahAPIError(Exception):
    pass


def _build_headers():
    api_key = settings.MYFATOORAH_API_KEY
    if not api_key:
        raise MyFatoorahConfigurationError("MYFATOORAH_API_KEY is not configured.")

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _call_myfatoorah(endpoint: str, payload: dict):
    base_url = settings.MYFATOORAH_BASE_URL
    if not base_url:
        raise MyFatoorahConfigurationError("MYFATOORAH_BASE_URL is not configured.")

    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    encoded_payload = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=encoded_payload, method="POST")

    headers = _build_headers()
    for key, value in headers.items():
        req.add_header(key, value)

    try:
        with request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {}
            return json.loads(body)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        raise MyFatoorahAPIError(body or str(exc)) from exc
    except error.URLError as exc:
        raise MyFatoorahAPIError(str(exc)) from exc


def create_payment_url(booking, payment):
    payment_method_id = getattr(payment, "selected_payment_method_id", None)
    effective_payment_method_id = payment_method_id or settings.MYFATOORAH_PAYMENT_METHOD_ID

    if effective_payment_method_id is None:
        payload = {
            "Order": {
                "Amount": float(payment.amount),
            },
            "IntegrationUrls": {
                "Redirection": settings.MYFATOORAH_HOSTED_REDIRECTION_URL,
            },
            "Language": "EN",
            "Customer": {
                "Name": booking.requesting_physician.full_name or booking.requesting_physician.email,
                "Email": booking.requesting_physician.email,
                "MobileNumber": booking.requesting_physician.phone_number or "00000000",
            },
            "MetaData": {
                "booking_reference": booking.booking_reference,
            },
        }

        response = _call_myfatoorah("v3/payments", payload)
        data = response.get("Data") or response.get("data") or {}

        payment_url = (
            data.get("PaymentURL")
            or data.get("PaymentUrl")
            or data.get("paymentURL")
            or data.get("paymentUrl")
            or data.get("url")
        )
        if not payment_url:
            raise MyFatoorahAPIError("MyFatoorah v3 did not return a payment URL.")

        return {
            "payment_url": payment_url,
            "provider_invoice_id": str(data.get("InvoiceId") or data.get("invoiceId") or ""),
            "provider_payment_id": str(data.get("PaymentId") or data.get("paymentId") or ""),
            "raw_request": payload,
            "raw_response": response,
        }

    payload = {
        "CustomerName": booking.requesting_physician.full_name or booking.requesting_physician.email,
        "DisplayCurrencyIso": settings.DEFAULT_CURRENCY,
        "MobileCountryCode": "+965",
        "CustomerMobile": booking.requesting_physician.phone_number or "00000000",
        "CustomerEmail": booking.requesting_physician.email,
        "InvoiceValue": float(payment.amount),
        "CallBackUrl": settings.MYFATOORAH_CALLBACK_URL,
        "ErrorUrl": settings.MYFATOORAH_ERROR_URL,
        "Language": "en",
        "CustomerReference": booking.booking_reference,
        "UserDefinedField": booking.booking_reference,
    }

    # If no method is forced, MyFatoorah hosted page will present available methods.
    if effective_payment_method_id is not None:
        payload["PaymentMethodId"] = int(effective_payment_method_id)

    response = _call_myfatoorah("v2/ExecutePayment", payload)
    data = response.get("Data") or {}

    payment_url = data.get("PaymentURL")
    if not payment_url:
        raise MyFatoorahAPIError("MyFatoorah did not return a payment URL.")

    return {
        "payment_url": payment_url,
        "provider_invoice_id": str(data.get("InvoiceId") or ""),
        "provider_payment_id": str(data.get("PaymentId") or ""),
        "raw_request": payload,
        "raw_response": response,
    }


def get_available_payment_methods(invoice_amount: float):
    payload = {
        "InvoiceAmount": float(invoice_amount),
        "CurrencyIso": settings.DEFAULT_CURRENCY,
    }
    response = _call_myfatoorah("v2/InitiatePayment", payload)
    data = response.get("Data") or {}
    methods = data.get("PaymentMethods") or []

    normalized_methods = []
    for method in methods:
        normalized_methods.append(
            {
                "payment_method_id": method.get("PaymentMethodId"),
                "payment_method_ar": method.get("PaymentMethodAr"),
                "payment_method_en": method.get("PaymentMethodEn"),
                "service_charge": method.get("ServiceCharge"),
                "total_amount": method.get("TotalAmount"),
                "is_direct_payment": method.get("IsDirectPayment"),
                "image_url": method.get("ImageUrl"),
            }
        )

    return normalized_methods


def get_payment_status(payment_id_or_invoice_id, key_type="InvoiceId"):
    payload = {
        "Key": str(payment_id_or_invoice_id),
        "KeyType": key_type,
    }
    return _call_myfatoorah("v2/GetPaymentStatus", payload)
