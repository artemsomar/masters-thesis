import type { ProjectAccess } from '../types/project';

const storageKey = 'blueprint-uc.project-access';

export const saveProjectAccess = (project: ProjectAccess): void =>
  localStorage.setItem(storageKey, JSON.stringify(project));

export const getProjectAccess = (projectId: string): ProjectAccess | null => {
  const raw = localStorage.getItem(storageKey);
  if (!raw) return null;
  try {
    const project = JSON.parse(raw) as ProjectAccess;
    return project.projectId === projectId && new Date(project.expiresAt).getTime() > Date.now()
      ? project
      : null;
  } catch {
    return null;
  }
};
