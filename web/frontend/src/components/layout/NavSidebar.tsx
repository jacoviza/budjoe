import { Link, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useTheme } from '../../context/ThemeContext';
import { api } from '../../api/client';
import styles from './NavSidebar.module.css';

export default function NavSidebar() {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const [dupGroups, setDupGroups] = useState<number | null>(null);

  const isActive = (path: string) => location.pathname.startsWith(path);

  useEffect(() => {
    api.getDuplicateStats()
      .then((s) => setDupGroups(s.total_groups))
      .catch(() => setDupGroups(null));
  }, [location.pathname]);

  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <h1 className={styles.title}>Finance</h1>
        <button
          onClick={toggleTheme}
          className={styles.themeToggle}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>
      <nav className={styles.nav}>
        <Link
          to="/accounts"
          className={isActive('/accounts') ? styles.navLinkActive : styles.navLink}
        >
          📊 Accounts
        </Link>
        <Link
          to="/notifications"
          className={
            isActive('/notifications') ? styles.navLinkActive : styles.navLink
          }
        >
          🔔 Notifications
        </Link>
        <Link
          to="/actions"
          className={isActive('/actions') ? styles.navLinkActive : styles.navLink}
        >
          ⚙️ Actions
        </Link>
        <Link
          to="/duplicates"
          className={isActive('/duplicates') ? styles.navLinkActive : styles.navLink}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <span>⚡ Duplicates</span>
          {dupGroups !== null && dupGroups > 0 && (
            <span style={{
              background: 'var(--warning-color)',
              color: '#000',
              borderRadius: '10px',
              padding: '1px 7px',
              fontSize: '11px',
              fontWeight: 700,
              minWidth: '20px',
              textAlign: 'center',
            }}>
              {dupGroups}
            </span>
          )}
        </Link>
      </nav>
    </aside>
  );
}
