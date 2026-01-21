import uuid
from django.contrib.auth.models import User
from apps.users.models import UserProfile


def get_or_create_visitor(request):
    visitor_id = request.session.get("visitor_id")

    if visitor_id:
        return User.objects.get(username=visitor_id)

    username = f"visitor_{uuid.uuid4().hex}"
    user = User.objects.create_user(username=username)
    user.profile.role = UserProfile.ROLE_VISITOR
    user.profile.save()

    request.session["visitor_id"] = username
    return user
