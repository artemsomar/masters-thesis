import { AlertTriangle, ArrowLeft, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { DiagramSessionStatus } from '../../../types/api';
import styles from './GenerationError.module.scss';

type Props = { status: Extract<DiagramSessionStatus, 'failed' | 'cancelled' | 'expired'> };

const messages: Record<Props['status'], string> = {
  failed: 'The server could not generate a diagram from this description.',
  cancelled: 'This generation session was cancelled.',
  expired: 'This generation session is no longer available.',
};

export const GenerationError = ({ status }: Props) => (
  <section className={styles.error} role="alert">
    <AlertTriangle size={34} />
    <h1>{status === 'failed' ? 'Could not generate the diagram' : 'Generation unavailable'}</h1>
    <p>{messages[status]}</p>
    <Link to="/">
      <RefreshCw size={16} />
      Start a new generation
    </Link>
    <Link className={styles.secondary} to="/">
      <ArrowLeft size={16} />
      Back to Generator
    </Link>
  </section>
);
