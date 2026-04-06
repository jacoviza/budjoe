# Bank Notification Rules

Each section defines one email notification source.
The agent reads this file before scanning Gmail.

---

## BHD

**Sender:** `notificaciones@bhd.com.do`

**Subject patterns (any match triggers extraction):**
- `Transacción con tu tarjeta BHD`
- `Cargo en tu tarjeta BHD`
- `Compra aprobada BHD`
- `Transaction approved`

**Gmail query:**
```
from:notificaciones@bhd.com.do (subject:Transacción OR subject:Cargo OR subject:"Compra aprobada" OR subject:"Transaction approved")
```

**Institution:** `BHD`
**Account type:** `credit_card`

**Extraction hints:**
- Merchant: look for "Comercio:", "Merchant:", or similar near the amount
- Amount: look for "Monto:", "Amount:", or "RD$" followed by a number; strip "RD$" and commas
- Currency: if "US$" or "USD" appears near the amount → `USD`; otherwise `DOP`
- Card last 4: look for "terminada en XXXX" or "ending in XXXX"
- tx_type: `debit` for purchases; `credit` if "reverso", "crédito", or "refund" appears
- datetime: look for "Fecha:", "Date:", or timestamp near top of email body

---

## Scotiabank

**Sender:** `alertas@scotiabank.com.do`

**Subject patterns (any match triggers extraction):**
- `Compra aprobada`
- `Cargo realizado`
- `Alerta de transacción`
- `Purchase approved`

**Gmail query:**
```
from:alertas@scotiabank.com.do (subject:"Compra aprobada" OR subject:"Cargo realizado" OR subject:"Alerta de transacción" OR subject:"Purchase approved")
```

**Institution:** `Scotiabank`
**Account type:** `credit_card`

**Extraction hints:**
- Merchant: look for "Establecimiento:", "Merchant:", or "Comercio:"
- Amount: look for "Valor:", "Monto:", or number preceded by "RD$" or "US$"
- Currency: `USD` if "US$" near amount, else `DOP`
- Card last 4: look for "tarjeta terminada en" or "card ending"
- tx_type: `debit` for purchases; `credit` if "reverso" or "crédito" appears
- datetime: look for "Fecha y Hora:" or "Date:"

---

## Banco Popular

**Sender:** `alertas@mail.bpd.com.do`

**Subject patterns (any match triggers extraction):**
- `Transacción realizada`
- `Cargo a tu tarjeta`
- `Compra con tu tarjeta Popular`
- `Notificación de transacción`

**Gmail query:**
```
from:alertas@mail.bpd.com.do (subject:"Transacción realizada" OR subject:"Cargo a tu tarjeta" OR subject:"Compra con tu tarjeta" OR subject:"Notificación de transacción")
```

**Institution:** `Banco Popular`
**Account type:** `credit_card`

**Extraction hints:**
- Merchant: look for "Lugar de compra:", "Comercio:", or "Merchant:"
- Amount: look for "Monto de la transacción:", preceded by "RD$" or "US$"
- Currency: `USD` if "US$" appears, else `DOP`
- Card last 4: look for "Tarjeta No." followed by asterisks and 4 digits
- tx_type: `debit` for purchases; `credit` for reversals
- datetime: look for "Fecha:" and "Hora:" fields

---

## Adding New Rules

1. Copy any section above as a template.
2. Update: sender address, subject patterns, Gmail query, institution name, account type, and extraction hints.
3. Run the scan workflow — the agent reads this file automatically and picks up the new rule.
