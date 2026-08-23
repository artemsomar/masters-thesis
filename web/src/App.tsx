import { RouterProvider } from 'react-router-dom';
import { AppHeader } from './components/layout/AppHeader';
import { router } from './router';

export const App = () => (
  <>
    <AppHeader />
    <RouterProvider router={router} />
  </>
);
