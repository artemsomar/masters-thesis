export type ProjectAccess = {
  projectId: string;
  projectToken: string;
  name: string;
  updatedAt: string;
  expiresAt: string;
};

export type Project = Omit<ProjectAccess, 'projectToken'> & {
  documentXml: string;
};

export type AvailableProjectRequest = Pick<ProjectAccess, 'projectId' | 'projectToken'>;
