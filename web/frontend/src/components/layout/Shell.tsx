import { ReactNode } from 'react';
import NavSidebar from './NavSidebar';
import styles from './Shell.module.css';

interface ShellProps {
  children: ReactNode;
}

export default function Shell({ children }: ShellProps) {
  return (
    <div className={styles.shell}>
      <NavSidebar />
      <main className={styles.main}>{children}</main>
    </div>
  );
}
