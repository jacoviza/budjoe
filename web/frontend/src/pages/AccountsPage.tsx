import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { Account } from '../types';
import styles from './AccountsPage.module.css';

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        setLoading(true);
        const data = await api.getAccounts();
        setAccounts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load accounts');
      } finally {
        setLoading(false);
      }
    };

    fetchAccounts();
  }, []);

  if (loading) {
    return <div className={styles.loading}>Loading accounts...</div>;
  }

  return (
    <div className={styles.container}>
      <h1>Accounts</h1>
      {error && <div className={styles.error}>{error}</div>}
      <div className={styles.grid}>
        {accounts.map((account) => (
          <Link
            key={account.id}
            to={`/accounts/${account.id}`}
            className={styles.card}
          >
            <div className={styles.cardHeader}>
              <div>
                <h3>{account.institution}</h3>
                <p className={styles.accountType}>{account.account_type}</p>
              </div>
              <div className={styles.balance}>
                {account.latest_balance !== null ? (
                  <>
                    <div className={styles.amount}>
                      {account.latest_balance.toLocaleString('en-US', {
                        style: 'currency',
                        currency: account.latest_balance_currency || 'DOP',
                      })}
                    </div>
                    {account.latest_statement_date && (
                      <div className={styles.date}>
                        as of {account.latest_statement_date}
                      </div>
                    )}
                  </>
                ) : (
                  <div className={styles.noBalance}>No balance</div>
                )}
              </div>
            </div>
            {account.account_product && (
              <div className={styles.cardBody}>
                <p>
                  <strong>{account.account_product}</strong>
                </p>
              </div>
            )}
            {account.account_number_last4 && (
              <div className={styles.cardFooter}>
                ****{account.account_number_last4}
              </div>
            )}
          </Link>
        ))}
      </div>
      {accounts.length === 0 && (
        <p className={styles.noAccounts}>No accounts found. Load some data first!</p>
      )}
    </div>
  );
}
