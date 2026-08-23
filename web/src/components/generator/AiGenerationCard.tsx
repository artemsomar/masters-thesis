import { Sparkles } from 'lucide-react';
import styles from './AiGenerationCard.module.scss';

export const AiGenerationCard = () => (
  <article className={styles.card}>
    <div className={styles.icon}>
      <Sparkles size={22} />
    </div>
    <h2>Generate with AI</h2>
    <p>
      Describe your system and let Blueprint UC propose a diagram. This flow is delivered in Sprint
      4.
    </p>
    <span>Coming next</span>
  </article>
);
