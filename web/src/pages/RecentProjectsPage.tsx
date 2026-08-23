import { useQuery } from '@tanstack/react-query';
import { Clock3, FolderOpen, LoaderCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getAvailableProjects } from '../api/projects';
import { ProjectSidebar } from '../components/layout/ProjectSidebar';
import { getProjectAccesses } from '../lib/project-access';
import { queryKeys } from '../api/query-keys';
import styles from './RecentProjectsPage.module.scss';

export const RecentProjectsPage = () => {
  const access = getProjectAccesses();
  const projects = useQuery({
    queryKey: queryKeys.availableProjects(access.map((project) => project.projectId)),
    queryFn: () => getAvailableProjects(access),
    enabled: access.length > 0,
  });
  const available = projects.data ?? [];
  return (
    <div className={styles.page}>
      <ProjectSidebar />
      <main className={styles.main}>
        <header>
          <p>24-hour retention</p>
          <h1>Recent Projects</h1>
        </header>
        {projects.isPending && access.length ? (
          <LoaderCircle className={styles.spin} size={24} />
        ) : null}
        {!projects.isPending && !available.length ? (
          <p className={styles.empty}>No available projects in this browser.</p>
        ) : null}
        <div className={styles.list}>
          {available.map((project) => (
            <article className={styles.card} key={project.projectId}>
              <FolderOpen size={22} />
              <div>
                <h2>{project.name}</h2>
                <span>
                  <Clock3 size={13} />
                  Updated {new Date(project.updatedAt).toLocaleString()}
                </span>
              </div>
              <Link to={`/editor/${project.projectId}`}>Open</Link>
            </article>
          ))}
        </div>
        {projects.isError ? (
          <p className={styles.error}>Could not load the available projects from the server.</p>
        ) : null}
      </main>
    </div>
  );
};
