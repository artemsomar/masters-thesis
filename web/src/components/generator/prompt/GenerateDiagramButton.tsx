import { LoaderCircle, Sparkles } from 'lucide-react';
import styles from './GenerateDiagramButton.module.scss';

type Props = { disabled: boolean; pending: boolean };

export const GenerateDiagramButton = ({ disabled, pending }: Props) => (
  <button className={styles.button} type="submit" disabled={disabled || pending}>
    {pending ? <LoaderCircle className={styles.spin} size={18} /> : <Sparkles size={18} />}
    {pending ? 'Creating session…' : 'Generate Use Case Diagram'}
  </button>
);
