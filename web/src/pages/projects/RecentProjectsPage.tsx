import { useQuery } from '@tanstack/react-query';
import { LoaderCircle } from 'lucide-react';
import { getAvailableProjects } from '../../api/projects';
import { ProjectSidebar } from '../../components/layout/ProjectSidebar';
import { getProjectAccesses } from '../../lib/projects/project-access';
import { queryKeys } from '../../api/query-keys';
import styles from './RecentProjectsPage.module.scss';
import { RecentProjectCard } from './RecentProjectCard';

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
        {!access.length || (!projects.isPending && !projects.isError && !available.length) ? (
          <p className={styles.empty}>No available projects in this browser.</p>
        ) : null}
        <div className={styles.list}>
          {available.map((project) => (
            <RecentProjectCard key={project.projectId} project={project} />
          ))}
        </div>
        {projects.isError ? (
          <div className={styles.error} role="alert">
            <p>Could not load the available projects from the server.</p>
            <button type="button" onClick={() => void projects.refetch()}>
              Try again
            </button>
          </div>
        ) : null}
      </main>
    </div>
  );
};
