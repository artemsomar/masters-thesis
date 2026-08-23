import { FilePlus2, PencilLine } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import styles from './ProjectSidebar.module.scss';

type Props = { projectName?: string; projectId?: string };

export const ProjectSidebar = ({ projectName = 'New project', projectId }: Props) => (
  <aside className={styles.sidebar}>
    <div className={styles.project}>
      <strong>{projectName}</strong>
      <span>Use Case Diagram</span>
    </div>
    <nav className={styles.navigation}>
      <NavLink
        to="/"
        className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
      >
        <FilePlus2 size={17} />
        Generator
      </NavLink>
      {projectId ? (
        <NavLink
          to={`/editor/${projectId}`}
          className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
        >
          <PencilLine size={17} />
          Editor
        </NavLink>
      ) : (
        <span className={styles.disabled}>
          <PencilLine size={17} />
          Editor
        </span>
      )}
    </nav>
  </aside>
);
