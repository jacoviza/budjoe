import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../../context/ThemeContext';
import styles from './NavSidebar.module.css';

export default function NavSidebar() {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  const isActive = (path: string) => location.pathname.startsWith(path);

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
      </nav>
    </aside>
  );
}
