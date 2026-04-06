# How to transform bank statements

The markdown file stored in `../02-load/` is the input. Extract the fields defined in
`bank-statement-fields.md` and write the output to:

```
../03-transform/account-statements/[period-end-YYYY-MM-DD]-[institution-slug]-[account-type].md
```

Example: `2026-03-31-bhd-savings.md`, `2026-01-12-bhd-credit-card.md`

---

## Output format

All statement files use **YAML frontmatter** for account-level fields, followed by one currency section per currency found in the statement.

### Single currency (checking / savings)

```markdown
---
financial_institution: BHD
account_type: savings
account_number_last4: 1234
period_start: 2026-03-01
period_end: 2026-03-31
---

## DOP

currency: DOP
account_balance: 45,200.00

### Transactions

| date | merchant | debit | credit |
|------|----------|-------|--------|
| 2026-03-02 | Supermercados Nacional | 1,247.39 | |
| 2026-03-05 | Nómina | | 50,000.00 |
```

### Multi-currency (credit card / loan / mortgage)

```markdown
---
financial_institution: BHD
account_type: credit_card
account_number_last4: 4449
period_start: 2025-12-13
period_end: 2026-01-12
---

## DOP

currency: DOP
account_balance: 11,052.53
cut_date: 2026-01-12
balance_at_cut: 11,052.53
payment_due_date: 2026-02-06

### Transactions

| date | merchant | debit | credit |
|------|----------|-------|--------|
| 2025-12-16 | PRICESMART DOMINICANA | 4,580.00 | |
| 2026-01-06 | CR PROMOCION TC | | 4,000.00 |

## USD

currency: USD
account_balance: 1.58
cut_date: 2026-01-12
balance_at_cut: 1.58
payment_due_date: 2026-02-06

### Transactions

| date | merchant | debit | credit |
|------|----------|-------|--------|
| 2026-01-12 | INTERESES FINANCIAMIENTO | 1.21 | |
```

### Named product (e.g. Scotiabank)

When the statement identifies a specific product name, add `account_product`:

```markdown
---
financial_institution: Scotiabank República Dominicana
account_type: credit_card
account_product: American Express AMEX SUMA CCN
account_number_last4: 1114
period_start: 2026-02-17
period_end: 2026-03-16
---
```

---

## Rules

1. **YAML frontmatter is mandatory** — always open and close with `---`.
2. **`account_number_last4`**: include when the statement shows a masked account or card number (`****1234`); omit entirely if not visible.
3. **`account_product`**: include only when the statement explicitly names a product; omit for generic accounts.
4. **Currency section headers** use `## [ISO code]` (e.g. `## DOP`, `## USD`).
5. **Summary fields** are bare `key: value` lines immediately after the `## CURRENCY` heading, before `### Transactions`.
6. **`### Transactions`** table columns: `date`, `merchant`, `debit`, `credit` — unchanged from prior format.
7. **For `checking` / `savings`**: omit `cut_date`, `balance_at_cut`, `payment_due_date`.
8. **For `credit_card`**: include `cut_date`, `balance_at_cut`, `payment_due_date`, and optionally `credit_limit`, `minimum_payment` when shown.
9. **For `savings`**: include `interest_rate_annual` and `apy` when shown.
10. Leave debit or credit cell **blank** (not zero) when a transaction is one-directional.
11. Monetary amounts: comma-separated thousands, two decimal places (`1,247.39`).
12. All dates: `YYYY-MM-DD`.
13. Non-currency sections (e.g. "Cuotas", installments) and optional `### Summary` period-totals tables may be preserved as-is at the end of a section — the loader ignores them.
