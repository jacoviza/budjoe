import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { Transaction, TransactionPage } from '../../types';
import styles from './TransactionTable.module.css';
import InlineEditCell from './InlineEditCell';

interface TransactionTableProps {
  accountId: number;
  onEditClick?: (tx: Transaction) => void;
  onMoveClick?: (tx: Transaction) => void;
}

export default function TransactionTable({
  accountId,
  onEditClick,
  onMoveClick,
}: TransactionTableProps) {
  const [page, setPage] = useState<TransactionPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [descriptionOverrides, setDescriptionOverrides] = useState<Record<number, string>>({});

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await api.getAccountTransactions(accountId, {
          limit,
          offset,
        });
        setPage(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load transactions');
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [accountId, limit, offset]);

  if (loading) return <div className={styles.loading}>Loading transactions...</div>;
  if (error) return <div className={styles.error}>{error}</div>;
  if (!page) return null;

  const hasNext = offset + limit < page.total;
  const hasPrev = offset > 0;

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Date</th>
            <th>Merchant</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Type</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {page.transactions.length > 0 ? (
            page.transactions.map((tx) => (
              <tr key={tx.id}>
                <td>{tx.date}</td>
                <td>{tx.merchant}</td>
                <td>
                  <InlineEditCell
                    value={descriptionOverrides[tx.id] !== undefined ? descriptionOverrides[tx.id] : tx.description}
                    onSave={async (v) => {
                      await api.updateTransaction(tx.id, { description: v });
                      setDescriptionOverrides((prev) => ({ ...prev, [tx.id]: v }));
                    }}
                    placeholder="Add description…"
                  />
                </td>
                <td className={styles.amount}>
                  {tx.amount.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}{' '}
                  {tx.currency}
                </td>
                <td>{tx.tx_type}</td>
                <td>
                  {tx.notification_status ? (
                    <span className={`${styles.badge} ${styles[tx.notification_status]}`}>
                      {tx.notification_status}
                    </span>
                  ) : (
                    <span className={styles.badgeGray}>statement</span>
                  )}
                </td>
                <td className={styles.actions}>
                  <button
                    onClick={() => onEditClick?.(tx)}
                    className={styles.buttonSmall}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => onMoveClick?.(tx)}
                    className={styles.buttonSmall}
                  >
                    Move
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={7} className={styles.noData}>
                No transactions
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <div className={styles.pagination}>
        <button
          onClick={() => setOffset(Math.max(0, offset - limit))}
          disabled={!hasPrev}
        >
          ← Previous
        </button>
        <span>
          Showing {offset + 1} to {Math.min(offset + limit, page.total)} of{' '}
          {page.total}
        </span>
        <button onClick={() => setOffset(offset + limit)} disabled={!hasNext}>
          Next →
        </button>
      </div>
    </div>
  );
}
