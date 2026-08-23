import { useMutation, useQueryClient } from '@tanstack/react-query';
import { submitClarificationAnswers } from '../../api/diagram-sessions';
import { queryKeys } from '../../api/query-keys';
import type {
  DiagramSessionAccess,
  DiagramSessionStatusResponse,
  SubmitClarificationAnswersRequest,
} from '../../types/api';

export const useSubmitClarificationAnswers = (session: DiagramSessionAccess) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SubmitClarificationAnswersRequest) =>
      submitClarificationAnswers(session.sessionId, session.sessionToken, payload),
    onSuccess: (response) => {
      queryClient.setQueryData<DiagramSessionStatusResponse>(
        queryKeys.diagramSessionStatus(session.sessionId),
        (current) => (current ? { ...current, status: response.status } : current),
      );
      void queryClient.invalidateQueries({
        queryKey: queryKeys.clarificationQuestions(session.sessionId),
      });
    },
  });
};
