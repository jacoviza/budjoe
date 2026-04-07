import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Transaction } from '../types';
import styles from './NotificationsPage.module.css';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await api.getPendingNotifications();
        setNotifications(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load notifications');
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  const toggleSelect = (id: number) => {
    const newSelected = new Set(selected);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelected(newSelected);
  };

  const toggleSelectAll = () => {
    if (selected.size === notifications.length && notifications.length > 0) {
      setSelected(new Set());
    } else {
      setSelected(new Set(notifications.map((n) => n.id)));
    }
  };

  const handleBulkAction = async (status: 'approved' | 'rejected') => {
    if (selected.size === 0) return;

    try {
      setUpdating(true);
      await api.bulkUpdateNotificationStatus(
        Array.from(selected),
        status
      );
      // Remove updated items from list
      setNotifications(
        notifications.filter((n) => !selected.has(n.id))
      );
      setSelected(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update notifications');
    } finally {
      setUpdating(false);
    }
  };

  const handleSingleApprove = async (id: number) => {
    try {
      await api.updateNotificationStatus(id, 'approved');
      setNotifications(notifications.filter((n) => n.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update notification');
    }
  };

  const handleSingleReject = async (id: number) => {
    try {
      await api.updateNotificationStatus(id, 'rejected');
      setNotifications(notifications.filter((n) => n.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update notification');
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading notifications...</div>;
  }

  return (
    <div className={styles.container}>
      <h1>Pending Notifications</h1>
      {error && <div className={styles.error}>{error}</div>}

      {selected.size > 0 && (
        <div className={styles.actionBar}>
          <span>
            {selected.size} selected
          </span>
          <button
            onClick={() => handleBulkAction('approved')}
            disabled={updating}
            className={styles.btnSuccess}
          >
            ✓ Approve Selected
          </button>
          <button
            onClick={() => handleBulkAction('rejected')}
            disabled={updating}
            className={styles.btnDanger}
          >
            ✕ Reject Selected
          </button>
        </div>
      )}

      {notifications.length > 0 ? (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={
                      selected.size > 0 &&
                      selected.size === notifications.length
                    }
                    onChange={toggleSelectAll}
                  />
                </th>
                <th>Date</th>
                <th>Merchant</th>
                <th>Amount</th>
                <th>Type</th>
                <th>Currency</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {notifications.map((tx) => (
                <tr key={tx.id} className={selected.has(tx.id) ? styles.selected : ''}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.has(tx.id)}
                      onChange={() => toggleSelect(tx.id)}
                    />
                  </td>
                  <td>{tx.date}</td>
                  <td>{tx.merchant}</td>
                  <td className={styles.amount}>
                    {tx.amount.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </td>
                  <td>{tx.tx_type}</td>
                  <td>{tx.currency}</td>
                  <td className={styles.actions}>
                    <button
                      onClick={() => handleSingleApprove(tx.id)}
                      className={styles.btnSmallSuccess}
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleSingleReject(tx.id)}
                      className={styles.btnSmallDanger}
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className={styles.empty}>
          <p>No pending notifications</p>
        </div>
      )}
    </div>
  );
}
