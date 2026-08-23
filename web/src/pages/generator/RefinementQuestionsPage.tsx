import { Link, useParams } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { RefinementQuestionsWorkspace } from '../../components/generator/generation/RefinementQuestionsWorkspace';
import { ProjectSidebar } from '../../components/layout/ProjectSidebar';
import { getAiSessionAccess } from '../../lib/generation/session-access';
import styles from './AiGeneratingPage.module.scss';

export const RefinementQuestionsPage = () => {
  const { sessionId } = useParams();
  const session = sessionId ? getAiSessionAccess(sessionId) : null;

  if (!session)
    return (
      <main className={styles.state}>
        <AlertTriangle size={28} />
        <h1>Generation session unavailable</h1>
        <p>Start a new generation to create a fresh session.</p>
        <Link to="/">Back to Generator</Link>
      </main>
    );

  return (
    <div className={styles.page}>
      <ProjectSidebar projectName="AI generation" />
      <RefinementQuestionsWorkspace session={session} />
    </div>
  );
};
