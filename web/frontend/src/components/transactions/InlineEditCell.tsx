import { useState, useRef } from 'react';
import styles from './InlineEditCell.module.css';

interface InlineEditCellProps {
  value: string | null;
  onSave: (value: string) => Promise<void>;
  placeholder?: string;
  allowEmpty?: boolean;
}

export default function InlineEditCell({
  value,
  onSave,
  placeholder = 'Add…',
  allowEmpty = true,
}: InlineEditCellProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value ?? '');
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const startEdit = () => {
    setDraft(value ?? '');
    setEditing(true);
    setTimeout(() => inputRef.current?.select(), 0);
  };

  const cancel = () => {
    setEditing(false);
    setDraft(value ?? '');
  };

  const save = async () => {
    const trimmed = draft.trim();
    if (trimmed === (value ?? '')) { cancel(); return; }
    if (!allowEmpty && !trimmed) { cancel(); return; }
    setSaving(true);
    try {
      await onSave(trimmed);
      setEditing(false);
    } catch {
      setDraft(value ?? '');
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') save();
    if (e.key === 'Escape') cancel();
  };

  if (editing) {
    return (
      <input
        ref={inputRef}
        className={styles.input}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={save}
        onKeyDown={handleKeyDown}
        disabled={saving}
        autoFocus
      />
    );
  }

  return (
    <button
      className={`${styles.btn} ${saving ? styles.saving : ''}`}
      onClick={startEdit}
      title="Click to edit"
    >
      {value ? (
        <span>{value}</span>
      ) : (
        <span className={styles.placeholder}>{placeholder}</span>
      )}
      <span className={styles.icon}>✎</span>
    </button>
  );
}
