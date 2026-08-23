import { useMutation } from '@tanstack/react-query';
import { ArrowRight, FilePlus2, LoaderCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { createProject } from '../../api/projects';
import { saveProjectAccess } from '../../lib/projects/project-access';
import styles from './ManualProjectCard.module.scss';

export const ManualProjectCard = () => {
  const navigate = useNavigate();
  const create = useMutation({
    mutationFn: () => createProject(),
    onSuccess: (project) => {
      saveProjectAccess(project);
      navigate(`/editor/${project.projectId}`);
    },
  });
  return (
    <article className={styles.card}>
      <div className={styles.icon}>
        <FilePlus2 size={22} />
      </div>
      <h2>Start from scratch</h2>
      <p>
        Create an empty project in the server, then open the editor. Your diagram is saved
        automatically for 24 hours.
      </p>
      <button type="button" onClick={() => create.mutate()} disabled={create.isPending}>
        {create.isPending ? (
          <LoaderCircle className={styles.spin} size={17} />
        ) : (
          <FilePlus2 size={17} />
        )}
        Create empty diagram <ArrowRight size={16} />
      </button>
      {create.isError && (
        <span className={styles.error}>
          Could not create the project. Check that the server is running.
        </span>
      )}
    </article>
  );
};
