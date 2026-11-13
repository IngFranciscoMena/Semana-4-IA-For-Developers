import json
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.shortcuts import render


EUR_PER_USD = Decimal("1.05")
EXCHANGE_RATES_TO_USD = {
    "USD": Decimal("1"),
    "EUR": Decimal("1") / EUR_PER_USD,
}
SOURCE_FIELDS = {
    "id": ("id", "transaction_id", "ref"),
    "amount": ("amount", "total"),
    "currency": ("currency", "currency_code"),
    "timestamp": ("timestamp", "created_at", "date"),
    "status": ("status", "state", "result"),
    "source": {"source"},
}

STATUS_MAP = {
    "success": "SUCCESS",
    "completed": "SUCCESS",
    "ok": "SUCCESS",
    "failed": "FAILED",
    "error": "FAILED",
    "fallido": "FAILED",
    "rechazado": "FAILED",
    "pending": "PENDING",
    "pendiente": "PENDING"
}


def get_source_value(transaction, field, required=True):
    for source_field in SOURCE_FIELDS[field]:
        if source_field in transaction:
            return transaction[source_field]
    if required:
        raise KeyError(field)
    return None


def parse_timestamp(value):
    timestamp = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(timestamp).isoformat()
    except ValueError:
        for date_format in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(timestamp, date_format).isoformat()
            except ValueError:
                continue
        raise ValueError("Fecha no válida")


def normalize_transaction(transaction, source):
    raw_amount = get_source_value(transaction, "amount")
    amount_text = str(raw_amount).replace("$", "").replace("€", "").replace(" ", "")
    amount_text = amount_text.replace(",", ".")
    amount = Decimal(amount_text)
    if not amount.is_finite():
        raise InvalidOperation

    raw_currency = get_source_value(transaction, "currency", required=False)
    if raw_currency is None:
        amount_string = str(raw_amount)
        if "€" in amount_string:
            raw_currency = "EUR"
        elif "$" in amount_string:
            raw_currency = "USD"
        else:
            raise KeyError("currency")
    source_currency = str(raw_currency).upper()
    exchange_rate = EXCHANGE_RATES_TO_USD[source_currency]
    amount_usd = (amount * exchange_rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    status_text = str(get_source_value(transaction, "status")).lower()
    status = STATUS_MAP[status_text]

    source_text = get_source_value(transaction, "source", required=False)

    return {
        "id": str(get_source_value(transaction, "id")),
        "amount": float(amount_usd),
        "currency": "USD",
        "timestamp": parse_timestamp(get_source_value(transaction, "timestamp")),
        "status": status,
        "source": str(source_text) if source_text is not None else str(source),
    }


def transaction_table_row(transaction, source, normalized=None):
    if normalized is not None:
        return {**normalized, "is_valid": True}

    values = {}
    if isinstance(transaction, dict):
        for field in SOURCE_FIELDS:
            for source_field in SOURCE_FIELDS[field]:
                if source_field in transaction:
                    values[field] = transaction[source_field]
                    break

    raw_amount = values.get("amount", "")
    raw_currency = values.get("currency")
    if raw_currency is None:
        if "€" in str(raw_amount):
            raw_currency = "EUR"
        elif "$" in str(raw_amount):
            raw_currency = "USD"

    raw_source = values.get("source")

    return {
        "id": str(values.get("id", "—")),
        "amount": str(raw_amount) if raw_amount != "" else "—",
        "currency": str(raw_currency or "—").upper(),
        "timestamp": str(values.get("timestamp", "—")),
        "status": str(values.get("status", "—")),
        "source": raw_source if raw_source is not None else str(source),
        "is_valid": False,
    }


def chart_style(values, colors):
    total = sum(values)
    if not total:
        return "background: conic-gradient(#dee2e6 0% 100%);"

    stops = []
    current = 0
    for value, color in zip(values, colors):
        if value:
            end = current + value / total * 100
            stops.append(f"{color} {current:.2f}% {end:.2f}%")
            current = end
    return f"background: conic-gradient({', '.join(stops)});"


def home(request):
    context = {
        "total_processed": 0,
        "total_valid": 0,
        "total_invalid": 0,
        "status_counts": {status: 0 for status in ("SUCCESS", "FAILED", "PENDING")},
        "currency_totals": {},
        "processed_transactions": [],
        "validity_chart_style": chart_style((0, 0), ("#198754", "#dc3545")),
        "status_chart_style": chart_style((0, 0, 0), ("#198754", "#dc3545", "#ffc107")),
        "error": None,
    }

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            context["error"] = "Selecciona un archivo JSON."
        else:
            try:
                transactions = json.loads(uploaded_file.read().decode("utf-8-sig"))
                if not isinstance(transactions, list):
                    raise ValueError("El contenido JSON debe ser una lista de transacciones.")
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
                context["error"] = str(error)
            else:
                context["total_processed"] = len(transactions)
                currency_totals = {}

                for transaction in transactions:
                    try:
                        normalized = normalize_transaction(transaction, uploaded_file.name)
                    except (KeyError, TypeError, ValueError, InvalidOperation):
                        context["total_invalid"] += 1
                        context["processed_transactions"].append(
                            transaction_table_row(transaction, uploaded_file.name)
                        )
                        continue

                    context["total_valid"] += 1
                    context["processed_transactions"].append(
                        transaction_table_row(transaction, uploaded_file.name, normalized)
                    )
                    context["status_counts"][normalized["status"]] += 1
                    currency_totals[normalized["currency"]] = (
                        currency_totals.get(normalized["currency"], Decimal("0"))
                        + Decimal(str(normalized["amount"]))
                    )

                context["currency_totals"] = currency_totals
                context["validity_chart_style"] = chart_style(
                    (context["total_valid"], context["total_invalid"]),
                    ("#198754", "#dc3545"),
                )
                context["status_chart_style"] = chart_style(
                    tuple(context["status_counts"].values()),
                    ("#198754", "#dc3545", "#ffc107"),
                )

    return render(request, "transacciones/index.html", context)
