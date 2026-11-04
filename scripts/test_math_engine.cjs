'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');

function boot(filename, initialStorage = []) {
  const html = fs.readFileSync(path.join(root, filename), 'utf8');
  const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)];
  for (const [, attrs, code] of scripts) {
    if (!attrs.includes('application/json')) new vm.Script(code, { filename });
  }
  const data = JSON.parse(scripts.find(([, attrs]) => attrs.includes('simulation-data'))[2]);
  const elements = new Map();
  const storage = new Map(initialStorage);
  function element(id) {
    if (!elements.has(id)) {
      const node = {
        textContent: '', innerHTML: '', value: '', hidden: false, open: false,
        dataset: {}, style: { setProperty() {} }, attributes: {},
        classList: { toggle() { return false; }, remove() {} },
        setAttribute(k, v) { this.attributes[k] = v; }, addEventListener() {},
        querySelectorAll() { return []; }, querySelector() { return element(`${id}-child`); },
        focus() {}, getBoundingClientRect() { return { top: 0, height: 0 }; },
        showModal() { this.open = true; }, close() { this.open = false; },
      };
      elements.set(id, node);
    }
    return elements.get(id);
  }
  element('simulation-data').textContent = JSON.stringify(data);
  const context = vm.createContext({
    document: { getElementById: element, documentElement: element('html'),
      querySelectorAll() { return []; }, querySelector() { return element('query'); }, addEventListener() {} },
    localStorage: { getItem: k => storage.get(k) ?? null, setItem: (k, v) => storage.set(k, v) },
    matchMedia: () => ({ matches: false, addEventListener() {} }),
    addEventListener() {}, scrollTo() {}, innerWidth: 1200, scrollY: 0,
    setTimeout() { return 1; }, clearTimeout() {}, setInterval() { return 1; }, clearInterval() {},
  });
  const engine = scripts.find(([, attrs, code]) => !attrs && code.includes('function scoreReport'))[2];
  // Expose the actual closure only in this VM fixture; published code is unmodified.
  const instrumented = engine.replace(/\}\)\(\);\s*$/, `
    globalThis.mathTest = { DATA, QUESTIONS, GRADED, STATE_KEY,
      get state() { return state; }, set state(value) { state = value; },
      blankState, restoreState, isCorrect, isComplete, statusOf, scoreReport,
      start, finish, renderQuestion, goToQuestion, answerChanged, requestSubmit, review, reset };
  })();`);
  vm.runInContext(instrumented, context, { filename, timeout: 5000 });
  return { app: context.mathTest, storage, element };
}

function plain(value) { return JSON.parse(JSON.stringify(value)); }

for (const filename of ['Ts_Sick_Boii_Matematika.html', 'Ts_Sick_Boii_Matematika_Modifikasi.html']) {
  const { app, element, storage } = boot(filename);
  assert.equal(app.GRADED.length, 10);
  assert.equal(element('setup-subtitle').textContent, 'Matematika · SMP/MTs · 10 nomor dinilai');
  assert.equal(app.state.status, 'idle');
  const q6 = app.QUESTIONS[5], q10 = app.QUESTIONS[9];

  for (const q of app.QUESTIONS.slice(0, 9)) {
    for (const letter of 'ABCDE') assert.equal(app.isCorrect(q, letter), letter === q.key);
    assert.equal(app.isCorrect(q, undefined), false);
  }
  for (let mask = 0; mask < 16; mask++) {
    const selected = [...'ABCD'].filter((_, i) => mask & (1 << i));
    assert.equal(app.isCorrect(q10, selected), mask === 11, `PGK selection ${selected}`);
  }
  assert.equal(app.isCorrect(q10, ['D', 'B', 'A']), true);
  assert.equal(app.isCorrect(q10, ['A', 'A', 'B', 'D']), false);

  element('participant-name').value = 'Math regression';
  app.start();
  assert.equal(app.state.status, 'running');
  for (const q of app.QUESTIONS) {
    app.goToQuestion(q.n);
    assert.equal(element('reading-title').textContent, app.DATA.stimuli[q.n - 1].sourceTitle);
    assert.equal(element('question-format').textContent, q.sourceForm);
    if (q.form === 'PG') {
      app.answerChanged({ dataset: { answer: String(q.n) }, value: q.key });
    } else {
      for (const value of q.key) app.answerChanged({ dataset: { answer: String(q.n) }, value, checked: true });
    }
  }
  assert.equal(app.state.answers[6], 'C');
  assert.deepEqual(plain(app.state.answers[10]), ['A', 'B', 'D']);
  assert.equal(app.scoreReport().percentage, 100);
  assert.deepEqual(plain(app.scoreReport().counts), { correct: 10, wrong: 0, incomplete: 0, empty: 0, excluded: 0 });
  app.requestSubmit();
  assert.match(element('submit-message').textContent, /Semua nomor yang dinilai telah terisi/);
  app.finish();
  assert.equal(app.state.status, 'finished');
  app.review(6);
  assert.match(element('question-body').innerHTML, /70 menit/);
  assert.match(element('question-body').innerHTML, /Kunci dari yoo.txt/);

  const restored = boot(filename, [...storage]);
  assert.equal(restored.app.state.status, 'finished');
  assert.equal(restored.app.scoreReport().percentage, 100);
  assert.equal(restored.app.state.answers[6], 'C');
  restored.app.state.answers[10] = ['A', 'B'];
  assert.equal(restored.app.scoreReport().percentage, 90);
  restored.app.state.answers[10] = ['A', 'B', 'C', 'D'];
  assert.equal(restored.app.scoreReport().percentage, 90);
  restored.app.state.answers[10] = [];
  assert.equal(restored.app.statusOf(q10), 'empty');

  const legacyKey = filename.includes('Modifikasi')
    ? 'ts-sick-boii-math-modified-attempt-81129cf5ae8d'
    : 'ts-sick-boii-math-original-attempt-6b54dea4a4f3';
  assert.notEqual(app.STATE_KEY, legacyKey);
  const legacy = boot(filename, [[legacyKey, JSON.stringify(app.state)], ['bi-attempt', 'preserve']]);
  assert.equal(legacy.app.state.status, 'idle');
  assert.equal(legacy.storage.get('bi-attempt'), 'preserve');
  const invalid = boot(filename, [[app.STATE_KEY, '{broken JSON']]);
  assert.equal(invalid.app.state.status, 'idle');
  app.reset();
  assert.equal(app.state.status, 'idle');
  assert.deepEqual(plain(app.state.answers), {});
  assert.equal(app.isCorrect(q6, 'C'), true);
  console.log(`${filename}: rendering, 10/10 score, PGK combinations, review, restore and reset passed.`);
}
