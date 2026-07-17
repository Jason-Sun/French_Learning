import shutil
import tempfile
import unittest
from pathlib import Path

from sil import SentenceIntelligenceEngine, SQLiteKnowledgeRepository


class SentenceIntelligenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = SentenceIntelligenceEngine(SQLiteKnowledgeRepository('data/wordbank/liens-knowledge.sqlite'))

    def labels(self, sentence):
        return [node.label for node in self.engine.analyze(sentence).nodes if node.type == 'grammar_construction']

    def test_passe_compose(self):
        self.assertIn('passé composé with être', self.labels('Je suis allé à Paris.'))

    def test_futur_proche(self):
        self.assertIn('futur proche', self.labels('Je vais apprendre le français.'))

    def test_negation(self):
        self.assertIn('negation', self.labels("Je n'aime pas le café."))

    def test_expression_with_inflected_auxiliary(self):
        result = self.engine.analyze('Il a besoin de temps.')
        self.assertIn('avoir besoin de', [node.label for node in result.nodes])

    def test_subject_pronoun_is_not_reflexive(self):
        self.assertNotIn('reflexive construction', self.labels('Nous sommes à Paris.'))

    def test_analysis_instance_can_be_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'graph.sqlite'
            shutil.copy('data/wordbank/liens-knowledge.sqlite', database)
            repo = SQLiteKnowledgeRepository(database)
            result = SentenceIntelligenceEngine(repo).analyze("Je n'aime pas le café.")
            repo.persist_analysis(result)
            row = repo.db.execute('SELECT engine_version, cache_status FROM sentence_analysis_instances WHERE id=?', (result.id,)).fetchone()
            self.assertEqual((row['engine_version'], row['cache_status']), ('sil-0.1.0', 'transient'))


if __name__ == '__main__':
    unittest.main()
