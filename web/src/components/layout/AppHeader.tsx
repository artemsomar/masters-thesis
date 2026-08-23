import { Box } from 'lucide-react';
import styles from './AppHeader.module.scss';

export const AppHeader = () => (
  <header className={styles.header}>
    <div className={styles.brand}>
      <Box size={19} strokeWidth={2.5} /> Blueprint UC
    </div>
  </header>
);
