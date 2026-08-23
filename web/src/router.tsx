import { createBrowserRouter } from 'react-router-dom';
import { EditorPage } from './pages/EditorPage';
import { AiGeneratingPage } from './pages/AiGeneratingPage';
import { GeneratorPage } from './pages/GeneratorPage';
import { ImportPage } from './pages/ImportPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { RecentProjectsPage } from './pages/RecentProjectsPage';

export const router = createBrowserRouter([
  { path: '/', element: <GeneratorPage /> },
  { path: '/generating/:sessionId', element: <AiGeneratingPage /> },
  { path: '/editor/:projectId', element: <EditorPage /> },
  { path: '/import', element: <ImportPage /> },
  { path: '/projects', element: <RecentProjectsPage /> },
  { path: '*', element: <NotFoundPage /> },
]);
