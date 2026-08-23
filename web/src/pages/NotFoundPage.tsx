import { Link } from 'react-router-dom';

export const NotFoundPage = () => (
  <main style={{ padding: '64px', textAlign: 'center' }}>
    <h1>Page not found</h1>
    <Link to="/">Go to Generator</Link>
  </main>
);
