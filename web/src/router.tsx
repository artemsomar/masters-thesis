import { createBrowserRouter } from 'react-router-dom';
import { EditorPage } from './pages/editor/EditorPage';
import { AiGeneratingPage } from './pages/generator/AiGeneratingPage';
import { GeneratorPage } from './pages/generator/GeneratorPage';
import { RefinementQuestionsPage } from './pages/generator/RefinementQuestionsPage';
import { ImportPage } from './pages/projects/ImportPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { RecentProjectsPage } from './pages/projects/RecentProjectsPage';

export const router = createBrowserRouter([
  { path: '/', element: <GeneratorPage /> },
  { path: '/generating/:sessionId', element: <AiGeneratingPage /> },
  { path: '/generating/:sessionId/questions', element: <RefinementQuestionsPage /> },
  { path: '/editor/:projectId', element: <EditorPage /> },
  { path: '/import', element: <ImportPage /> },
  { path: '/projects', element: <RecentProjectsPage /> },
  { path: '*', element: <NotFoundPage /> },
]);
