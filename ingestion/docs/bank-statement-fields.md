# What fields to extract from bank statements

## Header fields (once per statement, all account types)

| Field | Required | Description |
|-------|----------|-------------|
| `financial_institution` | Yes | Bank or institution name — usually the document header |
| `account_type` | Yes | One of: `checking`, `savings`, `credit_card`, `loan`, `mortgage` |
| `account_product` | If named | Product name shown on statement, e.g. "Scotiamax", "AMEX SUMA CCN" |
| `account_number_last4` | If visible | Last 4 digits of the account or card number shown on the statement |
| `period_start` | Yes | First day of the statement period (YYYY-MM-DD) |
| `period_end` | Yes | Last day of the statement period (YYYY-MM-DD) |

**`account_number_last4` rule:** Look for a masked account or card number in the statement header or summary area (e.g. `****1234`, `XXXX-4567`, `•••• 9999`). Extract only the last 4 digits. For credit cards this is the card number. For savings/checking this is the account number. **Omit the field entirely** if no account identifier is visible on the statement.

**`account_product` rule:** Include only when the statement explicitly names a product (e.g. "Cuenta de Ahorro Scotiamax", "American Express AMEX SUMA"). Omit for generic/unnamed accounts.

---

## Per-currency section (repeat for each currency present)

| Field | Account types | Description |
|-------|--------------|-------------|
| `currency` | All | ISO 4217 code (e.g. `DOP`, `USD`) |
| `account_balance` | All | Closing/current balance for this currency |
| `cut_date` | credit_card, loan, mortgage | Statement closing/cut date (YYYY-MM-DD) |
| `balance_at_cut` | credit_card, loan, mortgage | Outstanding balance as of cut date |
| `payment_due_date` | credit_card, loan, mortgage | Last day to pay without penalty (YYYY-MM-DD) |
| `credit_limit` | credit_card | Total credit limit for this currency |
| `minimum_payment` | credit_card | Minimum payment due |
| `interest_rate_annual` | savings, loan, mortgage | Annual interest rate (e.g. `0.15%`) |
| `apy` | savings | Annual percentage yield |

For `checking` and `savings`: omit all credit_card/loan/mortgage fields.

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

- Account holder personal information (full name, address, ID number)
- Full unmasked account or card numbers
- Marketing text, promotional offers
- Branch information
- Previous statement references
