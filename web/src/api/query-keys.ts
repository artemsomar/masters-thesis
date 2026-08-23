export const queryKeys = {
  project: (projectId: string) => ['project', projectId] as const,
  availableProjects: (projectIds: string[]) => ['available-projects', projectIds] as const,
  diagramSessionStatus: (sessionId: string) => ['diagram-session', sessionId] as const,
};
