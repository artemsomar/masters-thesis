import { LoaderCircle, Radio, RefreshCw } from 'lucide-react';
import type { DiagramSessionStatus } from '../../../types/api';
import styles from './GenerationProgress.module.scss';

const statusText: Record<DiagramSessionStatus, string> = {
  created: 'Preparing generation…',
  analyzing: 'Analyzing system description…',
  awaiting_answers: 'Waiting for clarifications…',
  generating_diagram: 'Generating use case diagram…',
  diagram_ready: 'Preparing your editable diagram…',
  failed: 'Generation failed.',
  cancelled: 'Generation was cancelled.',
  expired: 'This generation session has expired.',
};

type Props = { status: DiagramSessionStatus; streamConnected: boolean };

export const GenerationProgress = ({ status, streamConnected }: Props) => (
  <section className={styles.progress} aria-live="polite">
    <div className={styles.spinner}>
      <LoaderCircle size={38} />
    </div>
    <h1>{statusText[status]}</h1>
    <p>
      {streamConnected ? <Radio size={14} /> : <RefreshCw size={14} />}
      {streamConnected ? 'Live status connected' : 'Checking status with the server'}
    </p>
  </section>
);
