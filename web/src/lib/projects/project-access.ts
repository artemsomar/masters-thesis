import type { ProjectAccess } from '../../types/project';

const storageKey = 'blueprint-uc.project-access';

const readProjects = (): ProjectAccess[] => {
  const raw = localStorage.getItem(storageKey);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as ProjectAccess | ProjectAccess[];
    return (Array.isArray(parsed) ? parsed : [parsed])
      .filter((project) => new Date(project.expiresAt).getTime() > Date.now())
      .map(({ projectId, projectToken, name, updatedAt, expiresAt }) => ({
        projectId,
        projectToken,
        name,
        updatedAt,
        expiresAt,
      }));
  } catch {
    return [];
  }
};

const writeProjects = (projects: ProjectAccess[]): void =>
  localStorage.setItem(storageKey, JSON.stringify(projects));

export const saveProjectAccess = (project: ProjectAccess): void => {
  const otherProjects = readProjects().filter(({ projectId }) => projectId !== project.projectId);
  const access: ProjectAccess = {
    projectId: project.projectId,
    projectToken: project.projectToken,
    name: project.name,
    updatedAt: project.updatedAt,
    expiresAt: project.expiresAt,
  };
  writeProjects([access, ...otherProjects]);
};

export const getProjectAccesses = (): ProjectAccess[] => readProjects();

export const removeProjectAccess = (projectId: string): void =>
  writeProjects(readProjects().filter((project) => project.projectId !== projectId));

export const getProjectAccess = (projectId: string): ProjectAccess | null => {
  return readProjects().find((project) => project.projectId === projectId) ?? null;
};
