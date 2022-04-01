from django.urls import path
from blog.views import home, contact, my_tickets, profile, search, about_us, category, supcategory, add_blog, update_blog, blog_detail, my_blogs
from shop.views import help_video


urlpatterns = [
    path('', home, name='home'),
    path('contact/', contact, name='contact'),
    path('myticket/', my_tickets, name='my_ticket'),
    path('profile/', profile, name='my_profile'),
    path('about/', about_us, name='about'),
    path('search/', search, name='search'),
    path('category/<int:pk>', category, name='category'),
    path('supcategory/<int:pk>', supcategory, name='sup-category'),
    path('help/', help_video, name='help'),
    path('addblog/', add_blog, name='add-blog'),
    path('updateblog/<int:pk>', update_blog, name='update-blog'),
    path('blog/<int:pk>', blog_detail, name='blog-detail'),
    path('myblogs/', my_blogs, name='my-blogs'),
]
