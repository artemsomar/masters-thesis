import { Link, useParams } from 'react-router-dom';
import { AlertTriangle, LoaderCircle } from 'lucide-react';
import { EditorWorkspace } from '../components/editor/EditorWorkspace';
import { ProjectSidebar } from '../components/layout/ProjectSidebar';
import { useProject } from '../hooks/useProject';
import { getProjectAccess } from '../lib/project-access';
import styles from './EditorPage.module.scss';

export const EditorPage = () => {
  const { projectId } = useParams();
  if (!projectId) return <div className={styles.state}>Project not found.</div>;
  const access = getProjectAccess(projectId);
  const project = useProject(projectId);
  if (!access)
    return (
      <div className={styles.state}>
        <AlertTriangle size={26} />
        <h1>This project is unavailable</h1>
        <p>Its access key is missing or the 24-hour retention period has ended.</p>
        <Link to="/">Create a new diagram</Link>
      </div>
    );
  if (project.isPending)
    return (
      <div className={styles.state}>
        <LoaderCircle className={styles.spin} size={28} />
        Loading project…
      </div>
    );
  if (project.isError || !project.data)
    return (
      <div className={styles.state}>
        <AlertTriangle size={26} />
        <h1>Could not open the project</h1>
        <p>It may have expired or the server is unreachable.</p>
        <Link to="/">Back to Generator</Link>
      </div>
    );
  return (
    <div className={styles.editor}>
      <ProjectSidebar projectId={projectId} projectName={project.data.name} />
      <EditorWorkspace
        projectId={projectId}
        projectToken={access.projectToken}
        documentXml={project.data.documentXml}
        projectName={project.data.name}
      />
    </div>
  );
};
