import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Clock3, FolderOpen, PencilLine } from 'lucide-react';
import { Link } from 'react-router-dom';
import { renameProject } from '../../api/projects';
import { queryKeys } from '../../api/query-keys';
import { getProjectAccess, saveProjectAccess } from '../../lib/projects/project-access';
import type { Project } from '../../types/project';
import styles from './RecentProjectsPage.module.scss';

type Metadata = Omit<Project, 'documentXml'>;

export const RecentProjectCard = ({ project }: { project: Metadata }) => {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(project.name);
  const rename = useMutation({
    mutationFn: async (newName: string) => {
      const access = getProjectAccess(project.projectId);
      if (!access) throw new Error('The project has expired or its access key is missing.');
      const metadata = await renameProject(project.projectId, access.projectToken, newName);
      saveProjectAccess({ ...metadata, projectToken: access.projectToken });
      return metadata;
    },
    onSuccess: (metadata) => {
      queryClient.setQueriesData<Metadata[]>({ queryKey: ['available-projects'] }, (current) =>
        current?.map((item) => (item.projectId === metadata.projectId ? metadata : item)),
      );
      queryClient.setQueryData<Project>(queryKeys.project(metadata.projectId), (current) =>
        current ? { ...current, ...metadata } : undefined,
      );
      setEditing(false);
    },
  });

  return (
    <article className={styles.card}>
      <FolderOpen size={22} />
      <div className={styles.details}>
        {editing ? (
          <form
            className={styles.renameForm}
            onSubmit={(event) => {
              event.preventDefault();
              if (!name.trim() || rename.isPending) return;
              if (name.trim() === project.name) setEditing(false);
              else rename.mutate(name.trim());
            }}
          >
            <input
              aria-label="Project name"
              autoFocus
              value={name}
              maxLength={120}
              required
              disabled={rename.isPending}
              onChange={(event) => setName(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Escape' && !rename.isPending) setEditing(false);
              }}
            />
            <div className={styles.renameActions}>
              <button type="submit" disabled={!name.trim() || rename.isPending}>
                {rename.isPending ? 'Saving…' : 'Save'}
              </button>
              <button type="button" disabled={rename.isPending} onClick={() => setEditing(false)}>
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <h2>{project.name}</h2>
        )}
        <span>
          <Clock3 size={13} />
          Updated {new Date(project.updatedAt).toLocaleString()}
        </span>
        {editing && rename.isError ? (
          <p className={styles.renameError} role="alert">
            {rename.error.message}
          </p>
        ) : null}
      </div>
      <div className={styles.cardActions}>
        {!editing ? (
          <button
            type="button"
            aria-label={`Rename ${project.name}`}
            onClick={() => {
              setName(project.name);
              rename.reset();
              setEditing(true);
            }}
          >
            <PencilLine size={14} />
            Rename
          </button>
        ) : null}
        <Link to={`/editor/${project.projectId}`}>Open</Link>
      </div>
    </article>
  );
};
