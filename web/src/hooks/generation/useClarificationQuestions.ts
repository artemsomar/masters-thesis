import { useQuery } from '@tanstack/react-query';
import { getClarificationQuestions } from '../../api/diagram-sessions';
import { queryKeys } from '../../api/query-keys';
import type { DiagramSessionAccess } from '../../types/api';

export const useClarificationQuestions = (session: DiagramSessionAccess, enabled: boolean) =>
  useQuery({
    queryKey: queryKeys.clarificationQuestions(session.sessionId),
    queryFn: () => getClarificationQuestions(session.sessionId, session.sessionToken),
    enabled,
  });
