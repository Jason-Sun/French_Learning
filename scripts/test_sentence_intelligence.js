#!/usr/bin/env node
/* Focused deterministic regression checks for Sentence Intelligence. */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');

const root = path.resolve(__dirname, '..');
const context = { window: {} };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, 'sentence-intelligence.js'), 'utf8'), context);

const packageRoot = path.join(root, 'data/wordbank/browser');
const manifest = JSON.parse(fs.readFileSync(path.join(packageRoot, 'manifest.json'), 'utf8'));
const lookupPayload = fs.readFileSync(path.join(packageRoot, manifest.lookup.path));
if (crypto.createHash('sha256').update(lookupPayload).digest('hex') !== manifest.lookup.sha256) {
  throw new Error('Browser lookup checksum does not match its manifest.');
}
const objects = JSON.parse(lookupPayload).objects;
const engine = new context.window.SentenceIntelligence(objects);
const cases = [
  ['Je vais au cinéma ce soir.', [], 'vais — present indicative, person 1 singular of aller'],
  ['Nous allons à Paris.', []],
  ['Je vais partir ce soir.', ['Futur proche']],
  ['Nous allons manger.', ['Futur proche']],
];

for (const [sentence, expected, expectedForm] of cases) {
  const analysis = engine.analyze(sentence);
  const actual = analysis.grammar.map(node => node.label);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${sentence}: expected ${JSON.stringify(expected)}, received ${JSON.stringify(actual)}`);
  }
  if (expectedForm && !analysis.formAnalyses.some(node => node.label === expectedForm)) {
    throw new Error(`${sentence}: expected deterministic form analysis ${expectedForm}`);
  }
}

const contractionAnalysis = engine.analyze('Je vais au cinéma ce soir.');
if (!contractionAnalysis.contractions.some(node => node.label === 'au = à + le')) {
  throw new Error('Expected au to be exposed as the deterministic contraction à + le.');
}

console.log('Sentence Intelligence focused regression checks passed.');
