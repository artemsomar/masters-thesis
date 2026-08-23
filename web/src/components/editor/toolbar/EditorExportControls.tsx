import type Konva from 'konva';
import { Download, FileCode2, FileImage, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { downloadDataUrl, downloadTextFile } from '../../../lib/download';
import { stageToPng } from '../../../lib/png-export';
import { documentToSvg } from '../../../lib/svg-export';
import { documentToXml } from '../../../lib/xml';
import type { DiagramDocument } from '../../../types/diagram';
import styles from './EditorExportControls.module.scss';

type Props = { document: DiagramDocument; stageRef: React.RefObject<Konva.Stage | null> };

const filename = (extension: string) => `blueprint-use-case-diagram.${extension}`;

export const EditorExportControls = ({ document, stageRef }: Props) => (
  <div className={styles.controls} aria-label="Export diagram">
    <button
      type="button"
      onClick={() => downloadTextFile(filename('svg'), documentToSvg(document), 'image/svg+xml')}
    >
      <FileCode2 size={15} /> SVG
    </button>
    <button
      type="button"
      onClick={() => {
        if (stageRef.current) downloadDataUrl(filename('png'), stageToPng(stageRef.current));
      }}
    >
      <FileImage size={15} /> PNG
    </button>
    <button
      type="button"
      onClick={() => downloadTextFile(filename('xml'), documentToXml(document), 'application/xml')}
    >
      <FileText size={15} /> XML
    </button>
    <Link to="/import">
      <Download size={15} /> Import XML
    </Link>
  </div>
);
