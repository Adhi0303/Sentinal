from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from datetime import datetime, timezone
import uuid

app = FastAPI(
    title="Mock Core Banking API — Sentinel Razorpay Edition",
    description="Simulates Razorpay merchant banking operations and legacy AmEx endpoints.",
    version="2.0.0"
)

# CORS — allow Lovable and any local frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Rich In-Memory Mock Database — Consumer + Corporate Accounts
# ─────────────────────────────────────────────────────────────────────────────
accounts = {
    # Consumer Accounts (Customer Service Agent)
    "acc_123": {
        "name": "Sarah Johnson",
        "type": "CONSUMER",
        "status": "ACTIVE",
        "balance": 1000.0,
        "credit_limit": 5000.0,
        "years_as_customer": 5,
        "ytd_fees_waived": 30.0,
        "credit_score": 720,
        "transactions": [
            {"id": "txn_001", "date": "2026-07-20", "amount": -50.0,  "type": "LATE_FEE",  "description": "Late payment fee — July"},
            {"id": "txn_002", "date": "2026-07-22", "amount": -10.0,  "type": "LATE_FEE",  "description": "Overlimit fee"},
            {"id": "txn_003", "date": "2026-07-24", "amount":  500.0, "type": "PAYMENT",   "description": "Monthly payment received"},
        ]
    },
    "acc_456": {
        "name": "James Carter",
        "type": "CONSUMER",
        "status": "SUSPENDED",
        "balance": -250.0,
        "credit_limit": 1000.0,
        "years_as_customer": 0,
        "ytd_fees_waived": 220.0,
        "credit_score": 480,
        "transactions": [
            {"id": "txn_101", "date": "2026-07-18", "amount": -75.0,  "type": "LATE_FEE",    "description": "Late payment fee"},
            {"id": "txn_102", "date": "2026-07-20", "amount": -30.0,  "type": "LATE_FEE",    "description": "Overlimit fee"},
            {"id": "txn_103", "date": "2026-07-23", "amount": -50.0,  "type": "PENALTY_FEE", "description": "Returned check fee"},
        ]
    },
    # Corporate — Treasury Agent
    "corp_treasury_001": {
        "name": "American Express Treasury Division",
        "type": "CORPORATE",
        "status": "ACTIVE",
        "balance": 50_000_000.0,
        "credit_limit": 100_000_000.0,
        "years_as_customer": 20,
        "ytd_fees_waived": 0.0,
        "credit_score": 900,
        "transactions": [
            {"id": "txn_t001", "date": "2026-07-25", "amount": -2_500_000.0, "type": "SWEEP",   "description": "Overnight sweep to MM fund"},
            {"id": "txn_t002", "date": "2026-07-25", "amount":  1_000_000.0, "type": "RECEIPT", "description": "FX settlement — EUR/USD"},
        ]
    },
    # Vendor — Procurement Agent pays this
    "corp_vendor_aws": {
        "name": "Amazon Web Services LLC",
        "type": "VENDOR",
        "status": "ACTIVE",
        "balance": 0.0,
        "credit_limit": 0.0,
        "years_as_customer": 3,
        "ytd_fees_waived": 0.0,
        "credit_score": 900,
        "transactions": []
    },
    # Business — Underwriting Agent adjusts credit (good profile)
    "biz_456": {
        "name": "Meridian Consulting LLC",
        "type": "BUSINESS",
        "status": "ACTIVE",
        "balance": 85_000.0,
        "credit_limit": 10_000.0,
        "years_as_customer": 5,
        "ytd_fees_waived": 0.0,
        "credit_score": 820,
        "transactions": [
            {"id": "txn_b001", "date": "2026-07-10", "amount": -8_000.0, "type": "PURCHASE", "description": "Software licenses"},
            {"id": "txn_b002", "date": "2026-07-15", "amount":  8_000.0, "type": "PAYMENT",  "description": "Statement balance paid"},
        ]
    },
    # Business — Underwriting Agent adjusts credit (risky profile)
    "biz_789": {
        "name": "Sunrise Retail Inc",
        "type": "BUSINESS",
        "status": "PROBATION",
        "balance": -3_000.0,
        "credit_limit": 5_000.0,
        "years_as_customer": 0,
        "ytd_fees_waived": 0.0,
        "credit_score": 490,
        "transactions": [
            {"id": "txn_b101", "date": "2026-07-12", "amount": -5_000.0, "type": "PURCHASE", "description": "Inventory bulk order"},
            {"id": "txn_b102", "date": "2026-07-18", "amount":  -200.0,  "type": "LATE_FEE", "description": "Late payment fee"},
        ]
    },
    # Demo user 2 — Tara Williams (tara05)
    "acc_tara": {
        "name": "Tara Williams",
        "type": "CONSUMER",
        "status": "ACTIVE",
        "balance": 3_450.75,
        "credit_limit": 8_000.0,
        "years_as_customer": 3,
        "ytd_fees_waived": 0.0,
        "credit_score": 780,
        "transactions": [
            {"id": "txn_tw001", "date": "2026-07-01", "amount": -1_200.00, "type": "PURCHASE",  "description": "Online shopping — Amazon"},
            {"id": "txn_tw002", "date": "2026-07-05", "amount": -85.50,   "type": "PURCHASE",  "description": "Grocery store — Whole Foods"},
            {"id": "txn_tw003", "date": "2026-07-08", "amount":  2_500.00, "type": "PAYMENT",   "description": "Monthly payment received"},
            {"id": "txn_tw004", "date": "2026-07-12", "amount": -350.00,   "type": "PURCHASE",  "description": "Restaurant — The Capital Grille"},
            {"id": "txn_tw005", "date": "2026-07-15", "amount": -29.99,    "type": "LATE_FEE",  "description": "Late payment fee — July"},
            {"id": "txn_tw006", "date": "2026-07-18", "amount": -620.00,   "type": "PURCHASE",  "description": "Delta Airlines — flight booking"},
            {"id": "txn_tw007", "date": "2026-07-21", "amount":  1_000.00, "type": "PAYMENT",   "description": "Partial payment received"},
            {"id": "txn_tw008", "date": "2026-07-24", "amount": -45.25,    "type": "PURCHASE",  "description": "Spotify + Netflix subscriptions"},
        ]
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Razorpay Merchant Database (Module 9: Razorpay Pivot)
# ─────────────────────────────────────────────────────────────────────────────
razorpay_merchants = {
    "merch_zoopCart": {
        "name":            "Refund Merchant",
        "type":            "E_COMMERCE",
        "status":          "ACTIVE",
        "balance_inr":     2_50_000.0,   # ₹2,50,000
        "per_tx_limit":    10_000.0,      # ₹10,000 per refund
        "daily_refund_budget": 5_00_000.0,
        "currency":        "INR",
        "payments": [
            {"id": "pay_zoo001", "amount": 5_999.0,  "status": "CAPTURED",  "age_hours": 2,   "customer": "cust_a1", "method": "UPI"},
            {"id": "pay_zoo002", "amount": 2_499.0,  "status": "CAPTURED",  "age_hours": 24,  "customer": "cust_a2", "method": "CARD"},
            {"id": "pay_zoo003", "amount": 12_000.0, "status": "CAPTURED",  "age_hours": 48,  "customer": "cust_a3", "method": "NETBANKING"},
            {"id": "pay_zoo004", "amount": 9_800.0,  "status": "CAPTURED",  "age_hours": 5,   "customer": "cust_a4", "method": "UPI"},
            {"id": "pay_zoo005", "amount": 9_900.0,  "status": "CAPTURED",  "age_hours": 3,   "customer": "cust_a5", "method": "UPI"},
            {"id": "pay_zoo006", "amount": 9_750.0,  "status": "CAPTURED",  "age_hours": 1,   "customer": "cust_a6", "method": "CARD"},
            {"id": "pay_zoo007", "amount": 4_200.0,  "status": "REFUNDED",  "age_hours": 72,  "customer": "cust_a7", "method": "UPI"},
            {"id": "pay_zoo008", "amount": 1_100.0,  "status": "AUTHORIZED", "age_hours": 100, "customer": "cust_a8", "method": "WALLET"},
        ],
        "orders": [
            {"id": "order_z001", "amount": 5_999.0,  "status": "PAID",    "payment_id": "pay_zoo001", "created_at": "2026-08-22T09:00:00Z"},
            {"id": "order_z002", "amount": 2_499.0,  "status": "PAID",    "payment_id": "pay_zoo002", "created_at": "2026-08-21T10:00:00Z"},
            {"id": "order_z003", "amount": 12_000.0, "status": "PAID",    "payment_id": "pay_zoo003", "created_at": "2026-08-20T08:00:00Z"},
        ]
    },
    "merch_foodieApp": {
        "name":            "FoodieApp",
        "type":            "FOOD_DELIVERY",
        "status":          "ACTIVE",
        "balance_inr":     75_000.0,
        "per_tx_limit":    3_000.0,      # ₹3,000 per refund
        "daily_refund_budget": 50_000.0,
        "currency":        "INR",
        "payments": [
            {"id": "pay_food001", "amount": 850.0,  "status": "CAPTURED",   "age_hours": 1,   "customer": "cust_b1", "method": "UPI"},
            {"id": "pay_food002", "amount": 1_200.0, "status": "CAPTURED",  "age_hours": 12,  "customer": "cust_b2", "method": "CARD"},
            {"id": "pay_food003", "amount": 4_500.0, "status": "CAPTURED",  "age_hours": 6,   "customer": "cust_b3", "method": "NETBANKING"},
            {"id": "pay_food004", "amount": 320.0,   "status": "FAILED",    "age_hours": 2,   "customer": "cust_b4", "method": "UPI"},
        ],
        "orders": [
            {"id": "order_f001", "amount": 850.0,   "status": "DELIVERED",  "payment_id": "pay_food001", "created_at": "2026-08-22T10:00:00Z"},
            {"id": "order_f002", "amount": 1_200.0, "status": "CANCELLED",  "payment_id": "pay_food002", "created_at": "2026-08-22T06:00:00Z"},
        ]
    },
    "merch_saasHub": {
        "name":            "Fraud Merchant",
        "type":            "B2B_SAAS",
        "status":          "ACTIVE",
        "balance_inr":     18_00_000.0,   # ₹18,00,000
        "per_tx_limit":    50_000.0,       # ₹50,000
        "daily_refund_budget": 20_00_000.0,
        "currency":        "INR",
        "payments": [
            {"id": "pay_saas001", "amount": 49_999.0,  "status": "CAPTURED",  "age_hours": 24,   "customer": "cust_c1", "method": "CARD"},
            {"id": "pay_saas002", "amount": 12_500.0,  "status": "CAPTURED",  "age_hours": 72,   "customer": "cust_c2", "method": "NETBANKING"},
            {"id": "pay_saas003", "amount": 75_000.0,  "status": "AUTHORIZED", "age_hours": 130,  "customer": "cust_c3", "method": "CARD"},  # expired!
        ],
        "orders": [
            {"id": "order_s001", "amount": 49_999.0, "status": "ACTIVE", "payment_id": "pay_saas001", "created_at": "2026-08-21T08:00:00Z"},
        ]
    },
    "merch_quickPay": {
        "name":            "Settlement Merchant",
        "type":            "PAYMENT_AGGREGATOR",
        "status":          "ACTIVE",
        "balance_inr":     50_00_000.0,   # ₹50,00,000
        "per_tx_limit":    1_00_000.0,    # ₹1,00,000
        "daily_refund_budget": 1_00_00_000.0,
        "currency":        "INR",
        "payments": [
            {"id": "pay_qp001", "amount": 85_000.0,  "status": "CAPTURED",  "age_hours": 6,   "customer": "cust_d1", "method": "NEFT"},
            {"id": "pay_qp002", "amount": 5_50_000.0, "status": "AUTHORIZED", "age_hours": 2,  "customer": "cust_d2", "method": "RTGS"},
            {"id": "pay_qp003", "amount": 25_000.0,  "status": "CAPTURED",  "age_hours": 48,  "customer": "cust_d3", "method": "UPI"},
        ],
        "orders": []
    },
}

# Refund ledger — tracks processed refunds
refunds: dict = {}

# 2PC Reserve Ledger — tracks locked/reserved balances (Module 5.3)
reserves: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────────────────────────
class FeeWaiverRequest(BaseModel):
    account_id: str
    amount: float
    reason: str

class WireTransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float
    reference: str
    currency: str = "USD"

class CreditLimitRequest(BaseModel):
    account_id: str
    new_limit: float
    reason: str
    analyst_id: str

class ReserveRequest(BaseModel):
    account_id: str
    amount: float
    reserve_id: str

class CommitRequest(BaseModel):
    reserve_id: str
    action: str   # "COMMIT" or "ROLLBACK"

# ── Razorpay request models ───────────────────────────────────────────────────
class RefundRequest(BaseModel):
    payment_id: str
    amount: float
    reason: str = "customer_request"
    refund_destination: Optional[str] = None  # defaults to original source if None

class PayoutRequest(BaseModel):
    merchant_id: str
    amount: float
    destination_account: str
    destination_verified: bool = False
    reference: str
    currency: str = "INR"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _get_account(account_id: str) -> dict:
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found.")
    return accounts[account_id]

def _txn_id() -> str:
    return f"TXN-{uuid.uuid4().hex[:8].upper()}"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Original Endpoints (Module 3 — Agent Investigation Tools)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/v1/accounts/{account_id}")
def get_account_details(account_id: str):
    """Submodule 3: Agent investigation tool — fetch account status and profile."""
    acc = _get_account(account_id)
    return {
        "account_id":        account_id,
        "name":              acc["name"],
        "type":              acc.get("type", "CONSUMER"),
        "status":            acc["status"],
        "balance":           acc["balance"],
        "credit_limit":      acc.get("credit_limit", 0.0),
        "credit_score":      acc["credit_score"],
        "years_as_customer": acc["years_as_customer"],
        "ytd_fees_waived":   acc["ytd_fees_waived"],
    }

@app.get("/api/v1/accounts/{account_id}/transactions")
def get_transaction_history(account_id: str):
    """Submodule 3: Agent investigation tool — fetch last transactions."""
    acc = _get_account(account_id)
    return {"account_id": account_id, "transactions": acc["transactions"]}

@app.get("/api/v1/accounts/{account_id}/eligibility")
def check_waiver_eligibility(account_id: str):
    """Submodule 3: Agent investigation tool — is this account eligible for a waiver?"""
    acc = _get_account(account_id)
    reasons = []
    if acc["status"] != "ACTIVE":
        reasons.append(f"Account status is '{acc['status']}' (must be ACTIVE).")
    if acc["ytd_fees_waived"] >= 200.0:
        reasons.append(f"YTD fees already waived (${acc['ytd_fees_waived']}) exceeds annual limit of $200.")
    if acc["years_as_customer"] < 1:
        reasons.append("Account must be at least 1 year old to qualify.")
    eligible = len(reasons) == 0
    return {
        "account_id": account_id,
        "eligible":   eligible,
        "reasons":    reasons if not eligible else ["Account meets all waiver eligibility criteria."],
    }

@app.post("/api/v1/cards/fee-waiver")
def waive_fee(request: FeeWaiverRequest):
    """Core banking action — processes an approved fee waiver."""
    acc = _get_account(request.account_id)
    txn_id = _txn_id()
    accounts[request.account_id]["balance"]         += request.amount
    accounts[request.account_id]["ytd_fees_waived"] += request.amount
    accounts[request.account_id]["transactions"].append({
        "id": txn_id, "date": _now()[:10], "amount": request.amount,
        "type": "FEE_WAIVER", "description": f"Fee waiver: {request.reason}"
    })
    return {
        "status":         "SUCCESS",
        "transaction_id": txn_id,
        "message":        f"Fee of ${request.amount} waived for {request.account_id}",
        "new_balance":    accounts[request.account_id]["balance"],
        "processed_at":   _now(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Module 8.1: New Banking Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/v1/ledger/accounts/{account_id}/balance")
def get_balance(account_id: str):
    """Module 8.1: Real-time balance lookup. Used by Treasury and Procurement agents."""
    acc = _get_account(account_id)
    reserved = sum(
        r["amount"] for r in reserves.values()
        if r["account_id"] == account_id and r["status"] == "RESERVED"
    )
    return {
        "account_id":        account_id,
        "name":              acc["name"],
        "ledger_balance":    acc["balance"],
        "reserved_balance":  reserved,
        "available_balance": acc["balance"] - reserved,
        "currency":          "USD",
        "as_of":             _now(),
    }


@app.post("/api/v1/ledger/transfers/wire")
def wire_transfer(request: WireTransferRequest):
    """
    Module 8.1: Execute a wire transfer between accounts.
    Used by: Treasury Agent (intraday sweeps), Procurement Agent (vendor payments).
    Must be called via the Sentinel SDK — never directly.
    """
    from_acc = _get_account(request.from_account)
    _get_account(request.to_account)   # validate destination exists

    if from_acc["balance"] < request.amount:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient funds. Balance: ${from_acc['balance']:.2f}, Requested: ${request.amount:.2f}"
        )
    if from_acc["status"] not in ("ACTIVE",):
        raise HTTPException(
            status_code=422,
            detail=f"Source account status is '{from_acc['status']}'. Must be ACTIVE to transfer."
        )

    txn_id = _txn_id()
    accounts[request.from_account]["balance"] -= request.amount
    accounts[request.to_account]["balance"]   += request.amount
    accounts[request.from_account]["transactions"].append({
        "id": txn_id, "date": _now()[:10], "amount": -request.amount,
        "type": "WIRE_OUT", "description": f"Wire to {request.to_account}: {request.reference}"
    })
    accounts[request.to_account]["transactions"].append({
        "id": txn_id + "-IN", "date": _now()[:10], "amount": request.amount,
        "type": "WIRE_IN", "description": f"Wire from {request.from_account}: {request.reference}"
    })

    return {
        "status":            "SUCCESS",
        "transaction_id":    txn_id,
        "from_account":      request.from_account,
        "to_account":        request.to_account,
        "amount":            request.amount,
        "currency":          request.currency,
        "reference":         request.reference,
        "new_from_balance":  accounts[request.from_account]["balance"],
        "processed_at":      _now(),
    }


@app.post("/api/v1/credit/limit-increase")
def adjust_credit_limit(request: CreditLimitRequest):
    """
    Module 8.1: Adjust a customer's revolving credit limit.
    Used by: Underwriting Agent (credit line reviews).
    """
    acc = _get_account(request.account_id)
    if acc["status"] not in ("ACTIVE",):
        raise HTTPException(
            status_code=422,
            detail=f"Account status '{acc['status']}' — cannot adjust credit limit."
        )

    old_limit = acc["credit_limit"]
    accounts[request.account_id]["credit_limit"] = request.new_limit
    return {
        "status":       "SUCCESS",
        "account_id":   request.account_id,
        "old_limit":    old_limit,
        "new_limit":    request.new_limit,
        "delta":        round(request.new_limit - old_limit, 2),
        "reason":       request.reason,
        "approved_by":  request.analyst_id,
        "effective_at": _now(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Module 5.3: Two-Phase Commit Support Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/v1/ledger/reserve")
def reserve_funds(request: ReserveRequest):
    """2PC Phase 1 — Prepare: Lock/reserve funds before committing."""
    acc = _get_account(request.account_id)
    already_reserved = sum(
        r["amount"] for r in reserves.values()
        if r["account_id"] == request.account_id and r["status"] == "RESERVED"
    )
    available = acc["balance"] - already_reserved
    if available < request.amount:
        return {
            "status":    "INSUFFICIENT_FUNDS",
            "available": available,
            "requested": request.amount,
        }

    reserves[request.reserve_id] = {
        "account_id": request.account_id,
        "amount":     request.amount,
        "status":     "RESERVED",
        "created_at": _now(),
    }
    return {
        "status":                    "RESERVED",
        "reserve_id":                request.reserve_id,
        "amount":                    request.amount,
        "available_after_reserve":   available - request.amount,
    }


@app.post("/api/v1/ledger/commit")
def commit_reserve(request: CommitRequest):
    """
    2PC Phase 2 — Commit or Rollback a fund reservation.
    COMMIT:   Deducts the reserved amount from the real balance.
    ROLLBACK: Releases the reservation — funds become available again.
    """
    if request.reserve_id not in reserves:
        raise HTTPException(status_code=404, detail=f"Reserve '{request.reserve_id}' not found.")

    res = reserves[request.reserve_id]
    if res["status"] != "RESERVED":
        raise HTTPException(status_code=409, detail=f"Reserve '{request.reserve_id}' is already {res['status']}.")

    if request.action == "COMMIT":
        accounts[res["account_id"]]["balance"] -= res["amount"]
        reserves[request.reserve_id]["status"]  = "COMMITTED"
        return {
            "status":         "COMMITTED",
            "reserve_id":     request.reserve_id,
            "amount_deducted": res["amount"],
            "new_balance":    accounts[res["account_id"]]["balance"],
        }
    elif request.action == "ROLLBACK":
        reserves[request.reserve_id]["status"] = "ROLLED_BACK"
        return {
            "status":          "ROLLED_BACK",
            "reserve_id":      request.reserve_id,
            "amount_released": res["amount"],
        }

    raise HTTPException(status_code=400, detail="action must be 'COMMIT' or 'ROLLBACK'")


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/v1/accounts")
def list_accounts():
    """Returns all mock accounts (for dashboard and debugging)."""
    return {
        k: {"name": v["name"], "type": v["type"], "status": v["status"], "balance": v["balance"]}
        for k, v in accounts.items()
    }

@app.get("/health")
def health():
    return {"status": "OK", "service": "Mock Core Banking API", "port": 8000}


# ─────────────────────────────────────────────────────────────────────────────
# Module 5.3: Two-Phase Commit — Reservation List Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/ledger/reserves")
def list_reservations():
    """
    Returns all active (RESERVED) fund reservations.
    Used by the safety service to expose 2PC 'funds in transit'
    visibility to the operator dashboard.

    Returns only RESERVED status entries — COMMITTED and ROLLED_BACK
    are historical and not shown here.
    """
    active = {
        rid: res
        for rid, res in reserves.items()
        if res.get("status") == "RESERVED"
    }
    return {
        "count":        len(active),
        "reservations": {
            rid: {
                "account_id":  r["account_id"],
                "amount":      r["amount"],
                "reserved_at": r.get("reserved_at", "N/A"),
                "status":      "RESERVED",
            }
            for rid, r in active.items()
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 9: Razorpay-Native Endpoints
# ─────────────────────────────────────────────────────────────────────────────

def _get_merchant(merchant_id: str) -> dict:
    if merchant_id not in razorpay_merchants:
        raise HTTPException(status_code=404, detail=f"Merchant '{merchant_id}' not found.")
    return razorpay_merchants[merchant_id]

def _get_payment_from_any_merchant(payment_id: str) -> tuple:
    """Find a payment across all merchants. Returns (merchant_id, payment_dict)."""
    for mid, merch in razorpay_merchants.items():
        for pmt in merch.get("payments", []):
            if pmt["id"] == payment_id:
                return mid, pmt
    raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")


@app.get("/api/v1/merchants/{merchant_id}/balance")
def get_merchant_balance(merchant_id: str):
    """
    Module 9: Get real-time merchant settlement balance.
    Used by SettlementAgent and fraud analysis.
    """
    merch = _get_merchant(merchant_id)
    return {
        "merchant_id":     merchant_id,
        "name":            merch["name"],
        "type":            merch["type"],
        "status":          merch["status"],
        "balance_inr":     merch["balance_inr"],
        "per_tx_limit":    merch["per_tx_limit"],
        "currency":        merch.get("currency", "INR"),
        "as_of":           _now(),
    }


@app.get("/api/v1/merchants")
def list_merchants():
    """Module 9: List all registered Razorpay merchants."""
    return {
        "merchants": {
            mid: {
                "name":   m["name"],
                "type":   m["type"],
                "status": m["status"],
                "balance_inr": m["balance_inr"],
            }
            for mid, m in razorpay_merchants.items()
        }
    }


@app.post("/api/v1/payments/{payment_id}/refund")
def refund_payment(payment_id: str, request: RefundRequest):
    """
    Module 9: Process a refund for a captured Razorpay payment.
    Used by the RefundAgent. Must be called via Sentinel SDK.
    Business rules enforced here are a last-resort check; OPA Rego is the
    primary policy gate.
    """
    merchant_id, payment = _get_payment_from_any_merchant(payment_id)
    merch = razorpay_merchants[merchant_id]

    # Already refunded?
    if payment["status"] == "REFUNDED":
        raise HTTPException(status_code=409, detail=f"Payment '{payment_id}' has already been fully refunded.")
    # Failed payment?
    if payment["status"] == "FAILED":
        raise HTTPException(status_code=422, detail=f"Cannot refund a failed payment (status=FAILED).")
    # Not captured?
    if payment["status"] not in ("CAPTURED",):
        raise HTTPException(status_code=422, detail=f"Payment must be CAPTURED to refund. Current status: {payment['status']}.")
    # Amount check
    if request.amount > payment["amount"]:
        raise HTTPException(status_code=422, detail=f"Refund amount ({request.amount}) exceeds original payment ({payment['amount']}).")
    # Merchant balance check
    if request.amount > merch["balance_inr"]:
        raise HTTPException(status_code=422, detail=f"Insufficient merchant balance for refund.")

    refund_id = f"rfnd_{uuid.uuid4().hex[:8]}"
    razorpay_merchants[merchant_id]["balance_inr"] -= request.amount

    # Update payment status
    for i, pmt in enumerate(razorpay_merchants[merchant_id]["payments"]):
        if pmt["id"] == payment_id:
            razorpay_merchants[merchant_id]["payments"][i]["status"] = "REFUNDED"
            break

    refunds[refund_id] = {
        "refund_id":    refund_id,
        "payment_id":   payment_id,
        "merchant_id":  merchant_id,
        "amount":       request.amount,
        "reason":       request.reason,
        "status":       "PROCESSED",
        "processed_at": _now(),
    }

    return {
        "status":        "PROCESSED",
        "refund_id":     refund_id,
        "payment_id":    payment_id,
        "merchant_id":   merchant_id,
        "amount":        request.amount,
        "currency":      "INR",
        "original_payment_amount": payment["amount"],
        "merchant_balance_after":  razorpay_merchants[merchant_id]["balance_inr"],
        "processed_at":  _now(),
    }


@app.get("/api/v1/orders/{order_id}")
def get_order(order_id: str):
    """
    Module 9: Fetch order metadata by order ID across all merchants.
    Used by RefundAgent and SupportAgent to validate before processing.
    """
    for mid, merch in razorpay_merchants.items():
        for order in merch.get("orders", []):
            if order["id"] == order_id:
                return {
                    "order_id":   order_id,
                    "merchant_id": mid,
                    "merchant_name": merch["name"],
                    **order,
                }
    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")


@app.get("/api/v1/payments/{payment_id}")
def get_payment(payment_id: str):
    """
    Module 9: Fetch payment details by payment ID.
    Used by RefundAgent, SupportAgent, and FraudAnalysisAgent.
    """
    merchant_id, payment = _get_payment_from_any_merchant(payment_id)
    merch = razorpay_merchants[merchant_id]
    return {
        "payment_id":   payment_id,
        "merchant_id":  merchant_id,
        "merchant_name": merch["name"],
        "amount":        payment["amount"],
        "currency":      "INR",
        "status":        payment["status"],
        "age_hours":     payment["age_hours"],
        "customer_id":   payment["customer"],
        "method":        payment["method"],
        "per_tx_limit":  merch["per_tx_limit"],
        "already_refunded": payment["status"] == "REFUNDED",
    }


@app.get("/api/v1/refunds/{refund_id}")
def get_refund(refund_id: str):
    """Module 9: Fetch refund status by refund ID."""
    if refund_id not in refunds:
        raise HTTPException(status_code=404, detail=f"Refund '{refund_id}' not found.")
    return refunds[refund_id]


@app.get("/api/v1/merchants/{merchant_id}/payments")
def list_merchant_payments(merchant_id: str, status: Optional[str] = None):
    """Module 9: List all payments for a merchant, optionally filtered by status."""
    merch = _get_merchant(merchant_id)
    payments = merch.get("payments", [])
    if status:
        payments = [p for p in payments if p["status"].upper() == status.upper()]
    return {"merchant_id": merchant_id, "count": len(payments), "payments": payments}


@app.get("/api/v1/merchants/{merchant_id}/transactions")
def get_merchant_transactions(merchant_id: str):
    """Module 9: Fraud analysis view — all transactions for a merchant."""
    merch = _get_merchant(merchant_id)
    return {
        "merchant_id":  merchant_id,
        "name":         merch["name"],
        "payments":     merch.get("payments", []),
        "total_payments": len(merch.get("payments", [])),
        "total_volume":   sum(p["amount"] for p in merch.get("payments", [])),
    }


@app.post("/api/v1/payouts")
def initiate_payout(request: PayoutRequest):
    """
    Module 9: Initiate a merchant settlement payout.
    Used by SettlementAgent. Must be called via Sentinel SDK.
    Business rule: destination_verified must be True (mirrors razorpay_payout.rego).
    """
    merch = _get_merchant(request.merchant_id)

    # Hard block: destination not verified (last-resort check; OPA Rego is primary gate)
    if not request.destination_verified:
        raise HTTPException(
            status_code=422,
            detail="Payout destination is not verified. Verify destination account before initiating payout."
        )

    # Amount sanity
    if request.amount <= 0:
        raise HTTPException(status_code=422, detail="Payout amount must be greater than zero.")

    # Merchant balance check
    if request.amount > merch["balance_inr"]:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient merchant balance. Available: ₹{merch['balance_inr']:,.2f}, Requested: ₹{request.amount:,.2f}"
        )

    payout_id = f"po_{uuid.uuid4().hex[:8]}"
    razorpay_merchants[request.merchant_id]["balance_inr"] -= request.amount

    return {
        "status":              "PROCESSED",
        "payout_id":           payout_id,
        "merchant_id":         request.merchant_id,
        "merchant_name":       merch["name"],
        "amount":              request.amount,
        "currency":            request.currency,
        "destination_account": request.destination_account,
        "reference":           request.reference,
        "merchant_balance_after": razorpay_merchants[request.merchant_id]["balance_inr"],
        "processed_at":        _now(),
    }


@app.post("/api/v1/payments/{payment_id}/capture")
def capture_payment(payment_id: str, amount: float = None):
    """
    Module 9: Capture an AUTHORIZED Razorpay payment.
    Transitions payment from AUTHORIZED → CAPTURED, making it eligible for refund.
    Used by FraudAnalysisAgent to confirm legitimate transactions.
    """
    merchant_id, payment = _get_payment_from_any_merchant(payment_id)

    if payment["status"] != "AUTHORIZED":
        raise HTTPException(
            status_code=422,
            detail=f"Payment '{payment_id}' cannot be captured. Status: {payment['status']} (must be AUTHORIZED)."
        )

    capture_amount = amount if amount is not None else payment["amount"]
    if capture_amount > payment["amount"]:
        raise HTTPException(
            status_code=422,
            detail=f"Capture amount ({capture_amount}) exceeds authorized amount ({payment['amount']})."
        )

    # Transition to CAPTURED
    for i, pmt in enumerate(razorpay_merchants[merchant_id]["payments"]):
        if pmt["id"] == payment_id:
            razorpay_merchants[merchant_id]["payments"][i]["status"] = "CAPTURED"
            break

    return {
        "status":       "CAPTURED",
        "payment_id":   payment_id,
        "merchant_id":  merchant_id,
        "amount":       capture_amount,
        "currency":     "INR",
        "captured_at":  _now(),
        "message":      f"Payment {payment_id} captured successfully. Now eligible for refund.",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
