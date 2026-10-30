import { request } from './client';
import type { AvailableProjectRequest, Project, ProjectAccess } from '../types/project';

type CreateProjectResponse = ProjectAccess & { documentXml: string };

export const createProject = (name = 'Untitled diagram'): Promise<CreateProjectResponse> =>
  request('/api/v1/projects', { method: 'POST', body: JSON.stringify({ name }) });

export const getProject = (projectId: string, projectToken: string): Promise<Project> =>
  request(`/api/v1/projects/${projectId}`, {
    headers: { Authorization: `Bearer ${projectToken}` },
  });

export const updateProject = (
  projectId: string,
  projectToken: string,
  documentXml: string,
): Promise<Omit<Project, 'documentXml'>> =>
  request(`/api/v1/projects/${projectId}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${projectToken}` },
    body: JSON.stringify({ documentXml }),
  });

export const getAvailableProjects = (
  projects: AvailableProjectRequest[],
): Promise<Omit<ProjectAccess, 'projectToken'>[]> =>
  request('/api/v1/projects/available', {
    method: 'POST',
    body: JSON.stringify({ projects }),
  });

export const renameProject = (
  projectId: string,
  projectToken: string,
  name: string,
): Promise<Omit<Project, 'documentXml'>> =>
  request(`/api/v1/projects/${projectId}`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${projectToken}` },
    body: JSON.stringify({ name }),
  });
