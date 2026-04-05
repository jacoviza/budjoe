# How to transform bank statements

The markdown file stored in `../02-load/` is the input. Extract the fields defined in
`bank-statement-fields.md` and write the output to:

```
../03-transform/account-statements/[period-end-YYYY-MM-DD]-[institution-slug]-[account-type].md
```

Example: `2026-03-31-banco-popular-credit-card.md`

---

## Output format — single currency (checking / savings)

```markdown
# Account Statement — [Financial Institution]

## Header

| Field | Value |
|-------|-------|
| financial_institution | Banco Popular |
| account_type | checking |
| period_start | 2026-03-01 |
| period_end | 2026-03-31 |

## DOP

### Summary

| Field | Value |
|-------|-------|
| currency | DOP |
| account_balance | 45,200.00 |

### Transactions

| date | merchant | debit | credit |
|------|----------|-------|--------|
| 2026-03-02 | Supermercados Nacional | 1,247.39 | |
| 2026-03-05 | Nómina | | 50,000.00 |
```

---

## Output format — multi-currency (credit card / loan / mortgage)

```markdown
# Account Statement — [Financial Institution]

## Header

| Field | Value |
|-------|-------|
| financial_institution | Banco Popular |
| account_type | credit_card |
| period_start | 2026-03-01 |
| period_end | 2026-03-31 |

## DOP

### Summary

| Field | Value |
|-------|-------|
| currency | DOP |
| account_balance | 45,200.00 |
| cut_date | 2026-03-31 |
| balance_at_cut | 45,200.00 |
| payment_due_date | 2026-04-20 |

### Transactions

| date | merchant | debit | credit |
|------|----------|-------|--------|
| 2026-03-02 | Supermercados Nacional | 1,247.39 | |
| 2026-03-05 | Pago recibido | | 5,000.00 |

## USD

### Summary

| Field | Value |
|-------|-------|
| currency | USD |
| account_balance | 850.00 |
| cut_date | 2026-03-31 |
| balance_at_cut | 850.00 |
| payment_due_date | 2026-04-20 |

### Transactions

| date | merchant | debit | credit |
|------|----------|-------|--------|
| 2026-03-10 | Netflix | 15.99 | |
| 2026-03-15 | Payment | | 200.00 |
```

---

## Rules

1. If only one currency is present, emit one currency section — no need for separate headers.
2. For `checking` / `savings`: omit `cut_date`, `balance_at_cut`, and `payment_due_date` from the Summary.
3. Repeat the currency section pattern for every currency found in the statement.
4. Leave debit or credit cell blank (not zero) when a transaction only has one direction.
5. Monetary amounts use comma-separated thousands and two decimal places (e.g. `1,247.39`).
6. Dates always in YYYY-MM-DD format.
