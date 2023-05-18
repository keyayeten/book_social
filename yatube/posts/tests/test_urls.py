from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Group, Post
from http import HTTPStatus
from django.core.cache import cache

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)

    def test_index(self):
        # Отправляем запрос через client,
        # созданный в setUp()
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group(self):
        response = self.guest_client.get(
            f'/group/{StaticURLTests.group.slug}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_page(self):

        response = self.guest_client.get(
            f'/profile/{StaticURLTests.user.username}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail(self):
        response = self.guest_client.get(f'/posts/{StaticURLTests.post.pk}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        response = self.authorized_client.get(
            f'/posts/{StaticURLTests.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexciting(self):
        response = self.authorized_client.get('/ayee_coco_jambo')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            f'/group/{StaticURLTests.group.slug}/': 'posts/group_list.html',
            f'/posts/{StaticURLTests.post.pk}/': 'posts/post_detail.html',
            f'/profile/{StaticURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{StaticURLTests.post.pk}/edit/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
