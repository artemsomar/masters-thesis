import { useMutation } from '@tanstack/react-query';
import { getGeneratedDiagram } from '../../api/diagram-sessions';
import { createProject, updateProject } from '../../api/projects';
import { autoLayoutDocument } from '../../lib/diagram/auto-layout';
import { generatedDiagramToDocument } from '../../lib/diagram/generated-diagram-mapper';
import { saveProjectAccess } from '../../lib/projects/project-access';
import { documentToXml } from '../../lib/projects/xml';
import type { DiagramSessionAccess } from '../../types/api';

export const usePersistGeneratedDiagram = () =>
  useMutation({
    mutationFn: async (session: DiagramSessionAccess) => {
      const generated = await getGeneratedDiagram(session.sessionId, session.sessionToken);
      const document = await autoLayoutDocument(generatedDiagramToDocument(generated));
      const project = await createProject(generated.system.name);
      await updateProject(project.projectId, project.projectToken, documentToXml(document));
      saveProjectAccess(project);
      return project;
    },
  });
