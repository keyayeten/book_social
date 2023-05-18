from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='auth1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='test_comment',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_group_name = group.title
        self.assertEqual(expected_group_name, str(group))

        post = PostModelTest.post
        expected_post_name = post.text[:15]
        self.assertEqual(expected_post_name, str(post))

        self.assertEqual('auth - test_comment', str(PostModelTest.comment))

    def test_follow_creation(self):
        """Тест на создание объекта модели Follow."""

        follow = Follow.objects.create(user=PostModelTest.user,
                                       author=PostModelTest.user1)
        self.assertEqual(follow.user, PostModelTest.user)
        self.assertEqual(follow.author, PostModelTest.user1)

    def test_author_follower_list(self):
        """Тест на получение списка подписчиков автора."""
        user1 = PostModelTest.user
        user2 = PostModelTest.user1
        author = User.objects.create_user(username='testauthor')
        Follow.objects.create(user=user1, author=author)
        Follow.objects.create(user=user2, author=author)
        follower_list = author.following.all()
        self.assertEqual(follower_list.count(), 2)

    def test_user_following_list(self):
        """Тест на получение списка подписок пользователя."""
        user = PostModelTest.user
        author1 = PostModelTest.user1
        author2 = User.objects.create_user(username='testauthor2')
        Follow.objects.create(user=user, author=author1)
        Follow.objects.create(user=user, author=author2)
        following_list = user.follower.all()
        self.assertEqual(len(following_list), 2)

    def test_comment_creation(self):
        """Тест на создание объекта модели Comment."""
        user = PostModelTest.user
        post = PostModelTest.post
        comment = Comment.objects.create(author=user,
                                         post=post,
                                         text='test comment')
        self.assertEqual(comment.author, user)
        self.assertEqual(comment.post, post)
        self.assertEqual(comment.text, 'test comment')

    def test_post_comments_list(self):
        """Тест на получение списка комментариев к посту."""
        user = PostModelTest.user
        post = PostModelTest.post
        comment1 = Comment.objects.create(author=user,
                                          post=post,
                                          text='test comment 1')
        comment2 = Comment.objects.create(author=user,
                                          post=post,
                                          text='test comment 2')
        comments_list = post.comments.all()
        self.assertEqual(len(comments_list), 3)
        self.assertIn(comment1, comments_list)
        self.assertIn(comment2, comments_list)
