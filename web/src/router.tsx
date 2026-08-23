import { createBrowserRouter } from 'react-router-dom';
import { EditorPage } from './pages/EditorPage';
import { GeneratorPage } from './pages/GeneratorPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const router = createBrowserRouter([
  { path: '/', element: <GeneratorPage /> },
  { path: '/editor/:projectId', element: <EditorPage /> },
  { path: '*', element: <NotFoundPage /> },
]);
