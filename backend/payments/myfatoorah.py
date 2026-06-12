import json
import socket
from urllib import error, request
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


def _append_query_params(url: str, params: dict[str, str]) -> str:
    split = urlsplit(url)
    query = dict(parse_qsl(split.query, keep_blank_values=True))
    for key, value in params.items():
        value_text = str(value).strip()
        if value_text:
            query[key] = value_text
    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query), split.fragment))


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

    timeout_seconds = getattr(settings, "MYFATOORAH_REQUEST_TIMEOUT_SECONDS", 10)

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {}
            return json.loads(body)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        raise MyFatoorahAPIError(body or str(exc)) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise MyFatoorahAPIError("MyFatoorah request timed out.") from exc
    except error.URLError as exc:
        raise MyFatoorahAPIError(str(exc)) from exc


def create_payment_url(booking, payment):
    payment_method_id = getattr(payment, "selected_payment_method_id", None)
    effective_payment_method_id = payment_method_id or settings.MYFATOORAH_PAYMENT_METHOD_ID

    callback_url = _append_query_params(
        settings.MYFATOORAH_CALLBACK_URL,
        {"bookingReference": booking.booking_reference},
    )
    error_url = _append_query_params(
        settings.MYFATOORAH_ERROR_URL,
        {"bookingReference": booking.booking_reference},
    )

    payload = {
        "CustomerName": booking.requester_name,
        "DisplayCurrencyIso": settings.DEFAULT_CURRENCY,
        "MobileCountryCode": "+965",
        "CustomerMobile": booking.requester_whatsapp_number or booking.requesting_physician.phone_number or "00000000",
        "CustomerEmail": booking.requester_email,
        "InvoiceValue": float(payment.amount),
        "CallBackUrl": callback_url,
        "ErrorUrl": error_url,
        "Language": "en",
        "CustomerReference": booking.booking_reference,
        "UserDefinedField": booking.booking_reference,
    }
    payload["PaymentMethodId"] = int(effective_payment_method_id) if effective_payment_method_id is not None else 0

    try:
        response = _call_myfatoorah("v2/ExecutePayment", payload)
        data = response.get("Data") or {}

        payment_url = data.get("PaymentURL")
        if payment_url:
            return {
                "payment_url": payment_url,
                "provider_invoice_id": str(data.get("InvoiceId") or ""),
                "provider_payment_id": str(data.get("PaymentId") or ""),
                "raw_request": payload,
                "raw_response": response,
            }

        if effective_payment_method_id is not None:
            raise MyFatoorahAPIError("MyFatoorah did not return a payment URL.")
    except MyFatoorahAPIError:
        if effective_payment_method_id is not None:
            raise

    fallback_payload = {
        "Order": {
            "Amount": float(payment.amount),
            "CurrencyCode": settings.DEFAULT_CURRENCY,
        },
        "DisplayCurrencyIso": settings.DEFAULT_CURRENCY,
        "IntegrationUrls": {
            "Redirection": _append_query_params(
                settings.MYFATOORAH_HOSTED_REDIRECTION_URL,
                {"bookingReference": booking.booking_reference},
            ),
        },
        "Language": "EN",
        "Customer": {
            "Name": booking.requester_name,
            "Email": booking.requester_email,
            "MobileNumber": booking.requester_whatsapp_number or booking.requesting_physician.phone_number or "00000000",
        },
        "MetaData": {
            "booking_reference": booking.booking_reference,
        },
    }

    fallback_response = _call_myfatoorah("v3/payments", fallback_payload)
    fallback_data = fallback_response.get("Data") or fallback_response.get("data") or {}

    fallback_payment_url = (
        fallback_data.get("PaymentURL")
        or fallback_data.get("PaymentUrl")
        or fallback_data.get("paymentURL")
        or fallback_data.get("paymentUrl")
        or fallback_data.get("url")
    )
    if not fallback_payment_url:
        raise MyFatoorahAPIError("MyFatoorah did not return a payment URL.")

    return {
        "payment_url": fallback_payment_url,
        "provider_invoice_id": str(fallback_data.get("InvoiceId") or fallback_data.get("invoiceId") or ""),
        "provider_payment_id": str(fallback_data.get("PaymentId") or fallback_data.get("paymentId") or ""),
        "raw_request": fallback_payload,
        "raw_response": fallback_response,
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
