import assert from 'node:assert/strict';
import { beforeEach, test } from 'node:test';
import { registerHooks } from 'node:module';

const sourceRoot = new URL('../src/', import.meta.url).href;
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (
      context.parentURL?.startsWith(sourceRoot) &&
      specifier.startsWith('.') &&
      !/\.[a-z]+$/i.test(specifier)
    )
      specifier = new URL(`${specifier}.ts`, context.parentURL).href;
    return nextResolve(specifier, context);
  },
});
const { useDiagramStore: store } = await import('../src/store/diagram-store.ts');
const state = () => store.getState();
const fixture = () => ({
  schemaVersion: '1.0',
  nodes: [
    {
      id: 'actor',
      kind: 'actor',
      name: 'Member',
      description: '',
      position: { x: 0, y: 0 },
      style: { fill: '#fff', stroke: '#000', textColor: '#000' },
    },
    {
      id: 'case',
      kind: 'useCase',
      name: 'Borrow books',
      description: '',
      position: { x: 300, y: 0 },
      style: { fill: '#fff', stroke: '#000', textColor: '#000' },
    },
    {
      id: 'boundary',
      kind: 'boundary',
      name: 'Library',
      position: { x: 200, y: -100 },
      size: { width: 400, height: 300 },
      style: { fill: '#fff', stroke: '#000', textColor: '#000' },
    },
  ],
  relations: [{ id: 'link', type: 'association', sourceId: 'actor', targetId: 'case' }],
});
beforeEach(() => state().setDocument(fixture()));

test('undo and redo restore every property edit in order', () => {
  const original = structuredClone(state().document);
  state().updateNode('case', { name: 'Return books' });
  state().updateNode('case', { description: 'Return a borrowed book' });
  state().updateNode('case', { style: { ...state().document.nodes[1].style, fontSize: 18 } });
  state().updateNode('boundary', { name: 'Public library', size: { width: 500, height: 350 } });
  state().updateRelation('link', { type: 'include', targetAngle: -Math.PI / 2 });
  const edited = structuredClone(state().document);
  for (let i = 0; i < 5; i++) state().undo();
  assert.deepEqual(state().document, original);
  for (let i = 0; i < 5; i++) state().redo();
  assert.deepEqual(state().document, edited);
});

test('blurring unchanged fields preserves Redo and does not create history', () => {
  state().updateNode('case', { name: 'Return books' });
  state().undo();
  const revision = state().revision;
  state().updateNode('case', {
    name: 'Borrow books',
    description: '',
    style: { ...state().document.nodes[1].style },
  });
  state().updateNode('boundary', { size: { width: 400, height: 300 } });
  state().updateRelation('link', { type: 'association', sourceAngle: undefined });
  state().deleteElements(['missing']);
  assert.equal(state().revision, revision);
  assert.equal(state().past.length, 0);
  assert.equal(state().future.length, 1);
  state().redo();
  assert.equal(state().document.nodes[1].name, 'Return books');
});

test('one resize gesture creates one undo step', () => {
  const original = structuredClone(state().document);
  state().beginInteraction();
  state().resizeNodeLive('case', { x: 310, y: 10 }, { width: 200, height: 100 });
  state().resizeNodeLive('case', { x: 320, y: 20 }, { width: 250, height: 150 });
  assert.equal(state().revision, 0);
  state().commitInteraction();
  const edited = structuredClone(state().document);
  assert.equal(state().past.length, 1);
  state().undo();
  assert.deepEqual(state().document, original);
  state().redo();
  assert.deepEqual(state().document, edited);
});

test('endpoint dragging creates one undo step', () => {
  state().beginInteraction();
  state().moveRelationAnchorLive('link', 'target', 0.5);
  state().moveRelationAnchorLive('link', 'target', 1);
  state().commitInteraction();
  assert.equal(state().past.length, 1);
  state().undo();
  assert.equal(state().document.relations[0].targetAngle, undefined);
  state().redo();
  assert.equal(state().document.relations[0].targetAngle, 1);
});

test('deleting a node is undone together with its connections', () => {
  const original = structuredClone(state().document);
  state().deleteElements(['actor']);
  assert.equal(state().document.relations.length, 0);
  state().undo();
  assert.deepEqual(state().document, original);
  state().redo();
  assert.equal(
    state().document.nodes.some((node) => node.id === 'actor'),
    false,
  );
});

test('a new edit after Undo clears the redo branch', () => {
  state().updateNode('actor', { name: 'Reader' });
  state().undo();
  state().updateNode('actor', { name: 'Librarian' });
  assert.equal(state().future.length, 0);
  state().redo();
  assert.equal(state().document.nodes[0].name, 'Librarian');
});

test('empty interactions and empty history are harmless', () => {
  const original = structuredClone(state().document);
  state().undo();
  state().redo();
  state().beginInteraction();
  state().commitInteraction();
  assert.equal(state().revision, 0);
  assert.equal(state().past.length, 0);
  assert.equal(state().interactionSnapshot, undefined);
  assert.deepEqual(state().document, original);
});

test('opening another document resets all history and pending gestures', () => {
  state().updateNode('actor', { name: 'Reader' });
  state().beginInteraction();
  state().moveNodeLive('actor', { x: 80, y: 80 });
  state().setDocument(fixture());
  assert.equal(state().interactionSnapshot, undefined);
  assert.equal(state().past.length, 0);
  assert.equal(state().future.length, 0);
  state().commitInteraction();
  assert.equal(state().revision, 0);
});
