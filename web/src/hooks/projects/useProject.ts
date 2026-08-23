import { useQuery } from '@tanstack/react-query';
import { getProject } from '../../api/projects';
import { queryKeys } from '../../api/query-keys';
import { getProjectAccess } from '../../lib/projects/project-access';

export const useProject = (projectId: string) => {
  const access = getProjectAccess(projectId);
  return useQuery({
    queryKey: queryKeys.project(projectId),
    queryFn: () => getProject(projectId, access!.projectToken),
    enabled: Boolean(access),
  });
};
