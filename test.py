from unittest import TestCase
import mirror
import mock


class Test(TestCase):
    def test_url_to_filename(self):
        url = 'https://doc.scrapy.org/en/latest/index.html'
        self.assertEqual('index.html', mirror.url_to_filename(url))
        url = 'https://doc.scrapy.org/en/latest/'
        self.assertEqual('file', mirror.url_to_filename(url))

    def test_entity_filename(self):
        with mock.patch('mirror.entity_list', new=[2, 2]):
            entity = mirror.Entity(type='html', ext='html', url='https://doc.scrapy.org/en/latest/index.html')
            self.assertEqual('index-2.html', mirror.entity_filename(entity))


class TestEntity(TestCase):
    def test_relative_path(self):
        entity = mirror.Entity(type='html', filename='index.html', url='https://doc.scrapy.org/en/latest/index.html#hello')

        self.assertEqual('html/index.html', entity.relative_file_path)
        self.assertEqual('/html/index.html#hello', entity.url_path)

