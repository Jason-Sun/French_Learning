#!/usr/bin/env node
/* Focused deterministic regression checks for Sentence Intelligence. */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.resolve(__dirname, '..');
const context = { window: {} };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'sentence-intelligence.js'), 'utf8'), context);

const objects = JSON.parse(fs.readFileSync(path.join(root, 'data/wordbank/wordbank-index.json'), 'utf8')).objects;
const engine = new context.window.SentenceIntelligence(objects);
const cases = [
  ['Je vais au cinéma ce soir.', []],
  ['Nous allons à Paris.', []],
  ['Je vais partir ce soir.', ['Futur proche']],
  ['Nous allons manger.', ['Futur proche']],
];

for (const [sentence, expected] of cases) {
  const actual = engine.analyze(sentence).grammar.map(node => node.label);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${sentence}: expected ${JSON.stringify(expected)}, received ${JSON.stringify(actual)}`);
  }
}

console.log('Sentence Intelligence focused regression checks passed.');
