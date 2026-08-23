import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { createDiagramSession } from '../../api/diagram-sessions';
import { saveAiSessionAccess } from '../../lib/generation/session-access';
import { DescriptionEditor } from './prompt/DescriptionEditor';
import { GenerateDiagramButton } from './prompt/GenerateDiagramButton';
import { ManualProjectCard } from './ManualProjectCard';
import styles from './GeneratorWorkspace.module.scss';

export const GeneratorWorkspace = () => {
  const navigate = useNavigate();
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('en');
  const createSession = useMutation({
    mutationFn: () =>
      createDiagramSession({
        description: description.trim(),
        language,
        clarificationsEnabled: true,
      }),
    onSuccess: (session) => {
      saveAiSessionAccess(session);
      navigate(`/generating/${session.sessionId}`);
    },
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (description.trim()) createSession.mutate();
  };

  return (
    <main className={styles.main}>
      <section className={styles.content}>
        <header className={styles.heading}>
          <h1>Generate New Diagram</h1>
          <p>Describe the system and Blueprint UC will create an editable use case diagram.</p>
        </header>
        <div className={styles.workspace}>
          <form className={styles.generator} onSubmit={handleSubmit}>
            <DescriptionEditor
              value={description}
              disabled={createSession.isPending}
              onChange={setDescription}
            />
            <div className={styles.actions}>
              <label>
                <span>Result language</span>
                <select
                  value={language}
                  disabled={createSession.isPending}
                  onChange={(event) => setLanguage(event.target.value)}
                >
                  <option value="en">English</option>
                  <option value="uk">Ukrainian</option>
                </select>
              </label>
              <GenerateDiagramButton
                disabled={!description.trim()}
                pending={createSession.isPending}
              />
            </div>
            {createSession.isError ? (
              <p className={styles.error} role="alert">
                Could not create a generation session. Check that the server is available and try
                again.
              </p>
            ) : null}
          </form>
          <aside className={styles.manual}>
            <h2>Prefer manual modeling?</h2>
            <p>Create an empty, persistent project and edit it immediately.</p>
            <ManualProjectCard />
          </aside>
        </div>
      </section>
    </main>
  );
};
