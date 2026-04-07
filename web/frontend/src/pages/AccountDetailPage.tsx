import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { AccountDetail, Transaction } from '../types';
import TransactionTable from '../components/transactions/TransactionTable';
import TransactionEditModal from '../components/transactions/TransactionEditModal';
import MoveTransactionModal from '../components/transactions/MoveTransactionModal';
import styles from './AccountDetailPage.module.css';

export default function AccountDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [accountDetail, setAccountDetail] = useState<AccountDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [movingTx, setMovingTx] = useState<Transaction | null>(null);

  const accountId = id ? parseInt(id) : 0;

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await api.getAccount(accountId);
        setAccountDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load account');
      } finally {
        setLoading(false);
      }
    };

    if (accountId) {
      fetch();
    }
  }, [accountId]);

  const handleEditSave = (updatedTx: Transaction) => {
    setEditingTx(null);
    // Refresh account data
    if (accountDetail) {
      setAccountDetail({
        ...accountDetail,
        // The table will show the updated tx
      });
    }
  };

  const handleMoveSave = (updatedTx: Transaction) => {
    setMovingTx(null);
    // The transaction moved to a different account, refresh
    if (accountDetail) {
      setAccountDetail({
        ...accountDetail,
        // Remove the moved transaction from display
      });
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading account...</div>;
  }

  if (!accountDetail) {
    return <div className={styles.error}>Account not found</div>;
  }

  const { account, statements } = accountDetail;
  const latestStmt = statements[0];

  return (
    <div className={styles.container}>
      <button onClick={() => navigate('/accounts')} className={styles.backButton}>
        ← Back to Accounts
      </button>

      <div className={styles.header}>
        <div>
          <h1>{account.institution}</h1>
          <p className={styles.accountType}>{account.account_type}</p>
          {account.account_product && <p>{account.account_product}</p>}
        </div>
        {account.latest_balance !== null && (
          <div className={styles.balance}>
            <div className={styles.amount}>
              {account.latest_balance.toLocaleString('en-US', {
                style: 'currency',
                currency: account.latest_balance_currency || 'DOP',
              })}
            </div>
            {latestStmt && (
              <>
                {latestStmt.cut_date && (
                  <p>Cut: {latestStmt.cut_date}</p>
                )}
                {latestStmt.payment_due_date && (
                  <p>Due: {latestStmt.payment_due_date}</p>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.section}>
        <h2>Statements</h2>
        {statements.length > 0 ? (
          <div className={styles.statementsList}>
            {statements.map((stmt) => (
              <div key={stmt.id} className={styles.statement}>
                <strong>
                  {stmt.period_start} to {stmt.period_end} ({stmt.currency})
                </strong>
                <p>Balance: {stmt.account_balance}</p>
              </div>
            ))}
          </div>
        ) : (
          <p>No statements</p>
        )}
      </div>

      <div className={styles.section}>
        <h2>Transactions</h2>
        <TransactionTable
          accountId={accountId}
          onEditClick={setEditingTx}
          onMoveClick={setMovingTx}
        />
      </div>

      {editingTx && (
        <TransactionEditModal
          transaction={editingTx}
          onClose={() => setEditingTx(null)}
          onSave={handleEditSave}
        />
      )}

      {movingTx && (
        <MoveTransactionModal
          transaction={movingTx}
          onClose={() => setMovingTx(null)}
          onSave={handleMoveSave}
        />
      )}
    </div>
  );
}
