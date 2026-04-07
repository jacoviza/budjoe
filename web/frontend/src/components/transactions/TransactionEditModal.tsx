import { useState } from 'react';
import { api } from '../../api/client';
import { Transaction, TransactionUpdate } from '../../types';
import styles from './Modal.module.css';

interface TransactionEditModalProps {
  transaction: Transaction;
  onClose: () => void;
  onSave: (tx: Transaction) => void;
}

export default function TransactionEditModal({
  transaction,
  onClose,
  onSave,
}: TransactionEditModalProps) {
  const [merchant, setMerchant] = useState(transaction.merchant);
  const [date, setDate] = useState(transaction.date);
  const [amount, setAmount] = useState(transaction.amount.toString());
  const [txType, setTxType] = useState(transaction.tx_type);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    try {
      setSaving(true);
      const updates: TransactionUpdate = {};
      if (merchant !== transaction.merchant) updates.merchant = merchant;
      if (date !== transaction.date) updates.date = date;
      if (parseFloat(amount) !== transaction.amount) {
        updates.amount = parseFloat(amount);
      }
      if (txType !== transaction.tx_type) updates.tx_type = txType;

      const updated = await api.updateTransaction(transaction.id, updates);
      onSave(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update transaction');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={`${styles.modal} ${styles.open}`} onClick={onClose}>
      <div className={styles.content} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Edit Transaction</h2>
          <button className={styles.closeBtn} onClick={onClose}>
            ✕
          </button>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.body}>
          <div className={styles.formGroup}>
            <label>Merchant</label>
            <input
              type="text"
              value={merchant}
              onChange={(e) => setMerchant(e.target.value)}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Amount</label>
            <input
              type="number"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>

          <div className={styles.formGroup}>
            <label>Type</label>
            <select value={txType} onChange={(e) => setTxType(e.target.value)}>
              <option value="debit">Debit</option>
              <option value="credit">Credit</option>
            </select>
          </div>
        </div>

        <div className={styles.footer}>
          <button
            className={styles.btnSecondary}
            onClick={onClose}
            disabled={saving}
          >
            Cancel
          </button>
          <button
            className={styles.btnPrimary}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
