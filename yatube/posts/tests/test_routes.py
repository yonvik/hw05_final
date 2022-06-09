from django.test import TestCase
from django.urls import reverse

SLUG = 'slug'
USER = 'user'
POST_ID = 1

URLS = [
    ['/', 'index', ()],
    ['/create/', 'post_create', ()],
    [f'/group/{SLUG}/', 'group_list', (SLUG, )],
    [f'/profile/{USER}/', 'profile', (USER, )],
    [f'/posts/{POST_ID}/edit/', 'post_edit', (POST_ID, )],
    [f'/posts/{POST_ID}/', 'post_detail', (POST_ID, )],
    [f'/follow/', 'follow_index', ()]
]


class TaskPagesTests(TestCase):
    def test_pages_for_guests(self):
        """Тест маршрутов"""
        for url, route, args in URLS:
            with self.subTest(urls=url, route=route):
                self.assertEqual(url, reverse(f'posts:{route}', args=args))
