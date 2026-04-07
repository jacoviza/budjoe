import { useEffect, useState, useCallback, useRef } from 'react';
import { api } from '../api/client';
import { DuplicateGroup, DuplicateTransaction } from '../types';
import styles from './DuplicatesPage.module.css';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function sourceLabel(tx: DuplicateTransaction): string {
  if (tx.statement_id !== null) return 'statement';
  if (tx.notification_status !== null) return `notification`;
  return 'receipt';
}

function sourceBadgeClass(tx: DuplicateTransaction): string {
  if (tx.statement_id !== null) return styles.sourceBadgeStatement;
  if (tx.notification_status !== null) return styles.sourceBadgeNotification;
  return styles.sourceBadgeReceipt;
}

function formatAmount(amount: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'DOP',
    minimumFractionDigits: 2,
  }).format(amount);
}

function formatDate(iso: string): string {
  return iso.slice(0, 10);
}

// ─── Transaction column ────────────────────────────────────────────────────────

interface TxColProps {
  tx: DuplicateTransaction;
  merchantOverride?: string;
  descriptionOverride?: string | null;
  checked: boolean;
  onToggle: (id: number) => void;
  onMerchantSaved: (id: number, merchant: string) => void;
  onDescriptionSaved: (id: number, description: string) => void;
}

function useInlineEdit(
  current: string,
  onSave: (value: string) => Promise<void>,
  allowEmpty = false,
) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(current);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const startEdit = () => {
    setDraft(current);
    setEditing(true);
    setTimeout(() => inputRef.current?.select(), 0);
  };

  const cancel = () => { setEditing(false); setDraft(current); };

  const save = async () => {
    const trimmed = draft.trim();
    if (trimmed === current || (!allowEmpty && !trimmed)) { cancel(); return; }
    setSaving(true);
    try {
      await onSave(trimmed);
      setEditing(false);
    } catch {
      setDraft(current);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') save();
    if (e.key === 'Escape') cancel();
  };

  return { editing, draft, saving, inputRef, setDraft, startEdit, save, handleKeyDown };
}

function TxColumn({ tx, merchantOverride, descriptionOverride, checked, onToggle, onMerchantSaved, onDescriptionSaved }: TxColProps) {
  const displayMerchant = merchantOverride ?? tx.merchant;
  const displayDescription = descriptionOverride !== undefined ? descriptionOverride : tx.description;

  const merchant = useInlineEdit(displayMerchant, async (v) => {
    await api.updateTransaction(tx.id, { merchant: v });
    onMerchantSaved(tx.id, v);
  });

  const description = useInlineEdit(displayDescription ?? '', async (v) => {
    await api.updateTransaction(tx.id, { description: v });
    onDescriptionSaved(tx.id, v);
  }, true);

  return (
    <div className={styles.txCol}>
      <div className={styles.txColHeader}>
        <span className={styles.txIdChip}>#{tx.id}</span>
        <span className={`${styles.sourceBadge} ${sourceBadgeClass(tx)}`}>
          {sourceLabel(tx)}
        </span>
      </div>
      <div className={styles.txColBody}>
        <div className={styles.txField}>
          <span className={styles.txFieldLabel}>Merchant</span>
          {merchant.editing ? (
            <input
              ref={merchant.inputRef}
              className={styles.merchantInput}
              value={merchant.draft}
              onChange={(e) => merchant.setDraft(e.target.value)}
              onBlur={merchant.save}
              onKeyDown={merchant.handleKeyDown}
              disabled={merchant.saving}
              autoFocus
            />
          ) : (
            <button
              className={`${styles.merchantEditBtn} ${merchant.saving ? styles.merchantSaving : ''}`}
              onClick={merchant.startEdit}
              title="Click to edit merchant"
            >
              {displayMerchant}
              <span className={styles.editIcon}>✎</span>
            </button>
          )}
        </div>
        <div className={styles.txField}>
          <span className={styles.txFieldLabel}>Description</span>
          {description.editing ? (
            <input
              ref={description.inputRef}
              className={styles.merchantInput}
              value={description.draft}
              onChange={(e) => description.setDraft(e.target.value)}
              onBlur={description.save}
              onKeyDown={description.handleKeyDown}
              disabled={description.saving}
              autoFocus
            />
          ) : (
            <button
              className={`${styles.merchantEditBtn} ${description.saving ? styles.merchantSaving : ''}`}
              onClick={description.startEdit}
              title="Click to add description"
            >
              {displayDescription || <span className={styles.emptyFieldHint}>Add description…</span>}
              <span className={styles.editIcon}>✎</span>
            </button>
          )}
        </div>
        <div className={styles.txField}>
          <span className={styles.txFieldLabel}>Date</span>
          <span className={styles.txFieldValue}>{formatDate(tx.date)}</span>
        </div>
        <div className={styles.txField}>
          <span className={styles.txFieldLabel}>Amount</span>
          <span className={styles.txFieldValueMono}>
            {formatAmount(tx.amount, tx.currency)}
          </span>
        </div>
        <div className={styles.txField}>
          <span className={styles.txFieldLabel}>Type</span>
          <span className={styles.txFieldValue}>{tx.tx_type}</span>
        </div>
        {tx.notification_status && (
          <div className={styles.txField}>
            <span className={styles.txFieldLabel}>Status</span>
            <span className={styles.txFieldValue}>{tx.notification_status}</span>
          </div>
        )}
        <div className={styles.txField}>
          <span className={styles.txFieldLabel}>Imported</span>
          <span className={styles.txFieldValue}>{tx.imported_at.slice(0, 10)}</span>
        </div>
        <div className={styles.txField}>
          <span className={styles.txFieldLabel}>Mark duplicate</span>
          <input
            type="checkbox"
            checked={checked}
            onChange={() => onToggle(tx.id)}
            title={`Mark ID ${tx.id} as duplicate`}
            style={{ width: 16, height: 16, cursor: 'pointer', accentColor: 'var(--accent-color)' }}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Group card ────────────────────────────────────────────────────────────────

interface GroupCardProps {
  group: DuplicateGroup;
  onResolved: () => void;
  onSkip: () => void;
}

function GroupCard({ group, onResolved, onSkip }: GroupCardProps) {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [merchantOverrides, setMerchantOverrides] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [descriptionOverrides, setDescriptionOverrides] = useState<Record<number, string>>({});

  const handleMerchantSaved = (id: number, merchant: string) => {
    setMerchantOverrides((prev) => ({ ...prev, [id]: merchant }));
  };

  const handleDescriptionSaved = (id: number, desc: string) => {
    setDescriptionOverrides((prev) => ({ ...prev, [id]: desc }));
  };

  const txs = group.transactions;
  const allIds = txs.map((t) => t.id);
  const firstTx = txs[0];

  const toggleCheck = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const resolve = async (
    action: 'confirm_all' | 'dismiss_all' | 'confirm_selected',
  ) => {
    setBusy(true);
    setError(null);
    try {
      await api.resolveDuplicates({
        transaction_ids: allIds,
        action,
        selected_duplicate_ids:
          action === 'confirm_selected' ? [...selectedIds] : undefined,
      });
      onResolved();
    } catch (e: any) {
      setError(e.message ?? 'Unknown error');
      setBusy(false);
    }
  };

  const txCount = txs.length;

  return (
    <div className={styles.groupCard}>
      {/* Header */}
      <div className={styles.groupCardHeader}>
        <span className={styles.groupMerchant}>{firstTx.merchant}</span>
        <span className={styles.groupMeta}>
          {formatDate(firstTx.date)}
          {firstTx.account_label ? ` · ${firstTx.account_label}` : ''}
          {` · ${txCount} entries`}
        </span>
        <span className={styles.groupAmount}>
          {formatAmount(firstTx.amount, firstTx.currency)}
        </span>
      </div>

      {/* Transaction comparison grid */}
      <div
        className={styles.txGrid}
        style={{ '--tx-count': txCount } as React.CSSProperties}
      >
        {txs.map((tx) => (
          <TxColumn
            key={tx.id}
            tx={tx}
            merchantOverride={merchantOverrides[tx.id]}
            descriptionOverride={descriptionOverrides[tx.id]}
            checked={selectedIds.has(tx.id)}
            onToggle={toggleCheck}
            onMerchantSaved={handleMerchantSaved}
            onDescriptionSaved={handleDescriptionSaved}
          />
        ))}
      </div>

      {/* Error */}
      {error && <div className={styles.errorBox}>{error}</div>}

      {/* Action bar */}
      <div className={styles.actionBar}>
        <button
          className={styles.btnConfirm}
          disabled={busy}
          onClick={() => resolve('confirm_all')}
          title={`Keep ID ${allIds[0]} as original; mark the rest as duplicates`}
        >
          All duplicates
        </button>
        <button
          className={styles.btnDismiss}
          disabled={busy}
          onClick={() => resolve('dismiss_all')}
        >
          Not duplicates
        </button>
        {selectedIds.size > 0 && (
          <button
            className={styles.btnConfirmSelected}
            disabled={busy}
            onClick={() => resolve('confirm_selected')}
          >
            Mark {selectedIds.size} selected as duplicate{selectedIds.size > 1 ? 's' : ''}
          </button>
        )}
        {selectedIds.size === 0 && (
          <span className={styles.selectionHint}>
            or check rows above to mark specific ones
          </span>
        )}
        <button className={styles.btnSkip} disabled={busy} onClick={onSkip}>
          Skip →
        </button>
      </div>
    </div>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────────

export default function DuplicatesPage() {
  const [groups, setGroups] = useState<DuplicateGroup[]>([]);
  const [total, setTotal] = useState(0);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadGroups = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const page = await api.getDuplicateGroups({ limit: 100, offset: 0 });
      setGroups(page.groups);
      setTotal(page.total);
      setCurrentIdx(0);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load groups');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGroups();
  }, [loadGroups]);

  const handleResolved = () => {
    // Remove the resolved group from the local list
    setGroups((prev) => {
      const next = prev.filter((_, i) => i !== currentIdx);
      setTotal(next.length);
      // Stay at the same index (next group slides in), or go back if at end
      if (currentIdx >= next.length) {
        setCurrentIdx(Math.max(0, next.length - 1));
      }
      return next;
    });
  };

  const handleSkip = () => {
    setCurrentIdx((prev) => (prev + 1) % Math.max(groups.length, 1));
  };

  if (loading) {
    return (
      <div className="container">
        <div className={styles.loadingBox}>Loading duplicate groups…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className={styles.errorBox}>{error}</div>
      </div>
    );
  }

  const remaining = groups.length;
  const progressPct =
    total > 0 ? Math.round(((total - remaining) / total) * 100) : 100;

  return (
    <div className="container">
      {/* Page header */}
      <div className={styles.pageHeader}>
        <h2 className={styles.pageTitle}>Duplicate Transactions</h2>
        {remaining > 0 && (
          <span className={styles.groupBadge}>
            {remaining} group{remaining !== 1 ? 's' : ''} to review
          </span>
        )}
      </div>

      {/* Empty state */}
      {remaining === 0 && (
        <div className={styles.emptyState}>
          <span className={styles.emptyIcon}>✓</span>
          <p className={styles.emptyTitle}>All caught up!</p>
          <p className={styles.emptySubtitle}>
            No duplicate groups remaining. Your transaction data looks clean.
          </p>
        </div>
      )}

      {/* Progress bar */}
      {remaining > 0 && (
        <>
          <div className={styles.progress}>
            <span className={styles.progressLabel}>
              Group {currentIdx + 1} of {remaining}
            </span>
            <div className={styles.progressTrack}>
              <div
                className={styles.progressFill}
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <span className={styles.progressLabel}>{progressPct}% done</span>
          </div>

          {/* Navigation */}
          {remaining > 1 && (
            <div className={styles.navRow}>
              <button
                className={styles.navBtn}
                disabled={currentIdx === 0}
                onClick={() => setCurrentIdx((p) => p - 1)}
              >
                ← Previous
              </button>
              <span className={styles.navCounter}>
                {currentIdx + 1} / {remaining}
              </span>
              <button
                className={styles.navBtn}
                disabled={currentIdx >= remaining - 1}
                onClick={() => setCurrentIdx((p) => p + 1)}
              >
                Next →
              </button>
            </div>
          )}

          {/* Current group card */}
          {groups[currentIdx] && (
            <GroupCard
              key={groups[currentIdx].key}
              group={groups[currentIdx]}
              onResolved={handleResolved}
              onSkip={handleSkip}
            />
          )}
        </>
      )}
    </div>
  );
}
