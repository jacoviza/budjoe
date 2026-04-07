import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { Account, Transaction } from '../../types';
import styles from './Modal.module.css';

interface MoveTransactionModalProps {
  transaction: Transaction;
  onClose: () => void;
  onSave: (tx: Transaction) => void;
}

export default function MoveTransactionModal({
  transaction,
  onClose,
  onSave,
}: MoveTransactionModalProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState('');
  const [moving, setMoving] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const data = await api.getAccounts();
        setAccounts(data.filter((a) => a.id !== transaction.account_id));
        if (data.length > 0) {
          setSelectedAccountId(data[0].id.toString());
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load accounts');
      } finally {
        setLoading(false);
      }
    };

    fetchAccounts();
  }, [transaction.account_id]);

  const handleMove = async () => {
    if (!selectedAccountId) {
      setError('Please select a target account');
      return;
    }

    try {
      setMoving(true);
      const updated = await api.moveTransaction(
        transaction.id,
        parseInt(selectedAccountId)
      );
      onSave(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to move transaction');
    } finally {
      setMoving(false);
    }
  };

  return (
    <div className={`${styles.modal} ${styles.open}`} onClick={onClose}>
      <div className={styles.content} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Move Transaction</h2>
          <button className={styles.closeBtn} onClick={onClose}>
            ✕
          </button>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.body}>
          <p>
            Move <strong>{transaction.merchant}</strong> ({transaction.amount}{' '}
            {transaction.currency}) from account {transaction.account_id} to:
          </p>

          {loading ? (
            <p>Loading accounts...</p>
          ) : accounts.length > 0 ? (
            <div className={styles.formGroup}>
              <label>Target Account</label>
              <select
                value={selectedAccountId}
                onChange={(e) => setSelectedAccountId(e.target.value)}
              >
                <option value="">-- Select an account --</option>
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id.toString()}>
                    {acc.institution} - {acc.account_type}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <p>No other accounts available</p>
          )}
        </div>

        <div className={styles.footer}>
          <button
            className={styles.btnSecondary}
            onClick={onClose}
            disabled={moving}
          >
            Cancel
          </button>
          <button
            className={styles.btnPrimary}
            onClick={handleMove}
            disabled={moving || !selectedAccountId}
          >
            {moving ? 'Moving...' : 'Move'}
          </button>
        </div>
      </div>
    </div>
  );
}
