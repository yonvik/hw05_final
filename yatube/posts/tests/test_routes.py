from django.test import TestCase
from django.urls import reverse

from posts.urls import app_name

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
    ['/follow/', 'follow_index', ()],
    [f'/posts/{POST_ID}/comment/', 'add_comment', (POST_ID, )],
    [f'/profile/{USER}/follow/', 'profile_follow', (USER, )],
    [f'/profile/{USER}/unfollow/', 'profile_unfollow', (USER, )]

]


class TaskPagesTests(TestCase):
    def test_pages_for_guests(self):
        """Тест маршрутов"""
        for url, route, args in URLS:
            with self.subTest(urls=url, route=route):
                self.assertEqual(url,
                                 reverse(f'{app_name}:{route}', args=args))
