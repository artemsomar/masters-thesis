import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { FileUp, LoaderCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { createProject, updateProject } from '../api/projects';
import { ProjectSidebar } from '../components/layout/ProjectSidebar';
import { saveProjectAccess } from '../lib/project-access';
import { xmlToDocument } from '../lib/xml';
import styles from './ImportPage.module.scss';

const nameFromFile = (file: File) => file.name.replace(/\.xml$/i, '').trim() || 'Imported diagram';

export const ImportPage = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File>();
  const [error, setError] = useState<string>();
  const importProject = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('Choose an XML file first.');
      const xml = await file.text();
      xmlToDocument(xml);
      const project = await createProject(nameFromFile(file));
      await updateProject(project.projectId, project.projectToken, xml);
      return project;
    },
    onSuccess: (project) => {
      saveProjectAccess(project);
      navigate(`/editor/${project.projectId}`);
    },
    onError: (reason) =>
      setError(reason instanceof Error ? reason.message : 'Could not import XML.'),
  });
  return (
    <div className={styles.page}>
      <ProjectSidebar />
      <main className={styles.main}>
        <section className={styles.card}>
          <FileUp size={28} />
          <p className={styles.kicker}>Import diagram</p>
          <h1>Open a Blueprint UC XML file</h1>
          <p>The file is validated before a real 24-hour project is created on the server.</p>
          <label className={styles.fileInput}>
            <input
              type="file"
              accept="application/xml,.xml,text/xml"
              onChange={(event) => {
                setFile(event.target.files?.[0]);
                setError(undefined);
              }}
            />
            {file?.name ?? 'Choose XML file'}
          </label>
          <button
            type="button"
            disabled={!file || importProject.isPending}
            onClick={() => importProject.mutate()}
          >
            {importProject.isPending ? (
              <LoaderCircle className={styles.spin} size={17} />
            ) : (
              <FileUp size={17} />
            )}
            Import and open editor
          </button>
          {error ? <p className={styles.error}>{error}</p> : null}
        </section>
      </main>
    </div>
  );
};
