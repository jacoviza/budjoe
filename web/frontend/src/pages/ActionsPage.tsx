import { useState } from 'react';
import { api } from '../api/client';
import { ActionResult, PendingFilesResult } from '../types';
import styles from './ActionsPage.module.css';

export default function ActionsPage() {
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<PendingFilesResult | null>(null);

  const runAction = async (
    action: () => Promise<ActionResult>,
    actionName: string
  ) => {
    try {
      setLoading(true);
      const result = await action();
      setOutput(
        `[${actionName}]\n${
          result.return_code === 0
            ? '✓ Success'
            : `✕ Failed (exit code: ${result.return_code})`
        }\n\nSTDOUT:\n${result.stdout}\n\nSTDERR:\n${result.stderr}`
      );
    } catch (err) {
      setOutput(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const loadPendingFiles = async () => {
    try {
      setLoading(true);
      const files = await api.getPendingFiles();
      setPendingFiles(files);
      setOutput(
        `Pending Files:\n\nNotifications: ${files.notification_files.length}\n${files.notification_files.map((f) => `  - ${f}`).join('\n')}\n\nReceipt Transforms: ${files.receipt_transforms.length}\n${files.receipt_transforms.map((f) => `  - ${f}`).join('\n')}\n\nStatement Transforms: ${files.statement_transforms.length}\n${files.statement_transforms.map((f) => `  - ${f}`).join('\n')}`
      );
    } catch (err) {
      setOutput(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h1>Actions</h1>

      <div className={styles.section}>
        <h2>Database Migrations</h2>
        <div className={styles.buttonGroup}>
          <button
            onClick={() => runAction(() => api.runMigrate(), 'Migrate')}
            disabled={loading}
          >
            🔄 Run Migrations
          </button>
          <button
            onClick={() =>
              runAction(() => api.getMigrateStatus(), 'Migration Status')
            }
            disabled={loading}
          >
            📊 Migration Status
          </button>
        </div>
      </div>

      <div className={styles.section}>
        <h2>Load Data</h2>
        <div className={styles.buttonGroup}>
          <button
            onClick={() =>
              runAction(() => api.runLoadNotifications(), 'Load Notifications')
            }
            disabled={loading}
          >
            📬 Load Notifications
          </button>
          <button onClick={loadPendingFiles} disabled={loading}>
            📋 List Pending Files
          </button>
        </div>
      </div>

      {pendingFiles && (
        <div className={styles.section}>
          <h2>Pending Files Summary</h2>
          <div className={styles.pendingFiles}>
            <div className={styles.pendingGroup}>
              <strong>Bank Notifications ({pendingFiles.notification_files.length})</strong>
              {pendingFiles.notification_files.length > 0 ? (
                <ul>
                  {pendingFiles.notification_files.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : (
                <p className={styles.empty}>None</p>
              )}
            </div>

            <div className={styles.pendingGroup}>
              <strong>Receipt Transforms ({pendingFiles.receipt_transforms.length})</strong>
              {pendingFiles.receipt_transforms.length > 0 ? (
                <ul>
                  {pendingFiles.receipt_transforms.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : (
                <p className={styles.empty}>None</p>
              )}
            </div>

            <div className={styles.pendingGroup}>
              <strong>Statement Transforms ({pendingFiles.statement_transforms.length})</strong>
              {pendingFiles.statement_transforms.length > 0 ? (
                <ul>
                  {pendingFiles.statement_transforms.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : (
                <p className={styles.empty}>None</p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className={styles.section}>
        <h2>Output</h2>
        {output ? (
          <pre className={styles.output}>{output}</pre>
        ) : (
          <p className={styles.noOutput}>Run an action to see output here</p>
        )}
      </div>
    </div>
  );
}
