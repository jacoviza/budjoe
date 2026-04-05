# What fields to extract from bank statements

## Header fields (once per statement, all account types)

| Field | Description |
|-------|-------------|
| `financial_institution` | Bank or institution name — usually the document header |
| `account_type` | One of: `checking`, `savings`, `credit_card`, `loan`, `mortgage` |
| `period_start` | First day of the statement period (YYYY-MM-DD) |
| `period_end` | Last day of the statement period (YYYY-MM-DD) |

---

## Per-currency section (repeat for each currency present)

| Field | Description |
|-------|-------------|
| `currency` | ISO 4217 code (e.g. `DOP`, `USD`) |
| `account_balance` | Closing/current balance for this currency |

**Additional fields for `credit_card`, `loan`, `mortgage` only:**

| Field | Description |
|-------|-------------|
| `cut_date` | Statement closing/cut date (YYYY-MM-DD) |
| `balance_at_cut` | Outstanding balance as of the cut date (this currency) |
| `payment_due_date` | Last day to pay without penalty (YYYY-MM-DD) |

For `checking` and `savings`: omit `cut_date`, `balance_at_cut`, and `payment_due_date`.

---

## Per-transaction (listed under their currency section)

| Field | Description |
|-------|-------------|
| `date` | Transaction date (YYYY-MM-DD) |
| `merchant` | Merchant name or transaction description |
| `debit` | Amount charged/debited — leave blank if not applicable |
| `credit` | Amount credited/deposited — leave blank if not applicable |

---

## What NOT to extract

- Account holder name or personal information
- Full account numbers (partial/masked is fine as context)
- Marketing text, promotional offers
- Branch information
- Previous statement references
