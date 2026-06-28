from app.models import SocialLink

def social_links(request):
    return {
        'social_links': SocialLink.objects.all().order_by('order')
    }