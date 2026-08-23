import { GeneratorWorkspace } from '../../components/generator/GeneratorWorkspace';
import { ProjectSidebar } from '../../components/layout/ProjectSidebar';
import styles from './GeneratorPage.module.scss';

export const GeneratorPage = () => (
  <div className={styles.page}>
    <ProjectSidebar />
    <GeneratorWorkspace />
  </div>
);
