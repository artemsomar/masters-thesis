import { AiGenerationCard } from './AiGenerationCard';
import { ManualProjectCard } from './ManualProjectCard';
import styles from './GeneratorWorkspace.module.scss';

export const GeneratorWorkspace = () => (
  <main className={styles.main}>
    <section className={styles.content}>
      <p className={styles.kicker}>Use Case Diagram Builder</p>
      <h1>Generate a new diagram</h1>
      <p className={styles.lead}>
        Start with an empty, persistent project and build its system boundaries, actors and use
        cases manually.
      </p>
      <div className={styles.cards}>
        <ManualProjectCard />
        <AiGenerationCard />
      </div>
    </section>
  </main>
);
