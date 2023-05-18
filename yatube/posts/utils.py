from django.core.paginator import Paginator


def create_pagination(request, posts, NUM_OF_POSTS):
    paginator = Paginator(posts, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
