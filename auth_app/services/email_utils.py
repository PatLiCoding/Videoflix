import django_rq
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator

from auth_app.services.tokens import account_activation_token


def _send_html_email(subject, template_name, context, to_email):
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(
        subject, text_content, settings.DEFAULT_FROM_EMAIL, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_activation_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_link = (
        f"{settings.FRONTEND_URL}/pages/auth/activate.html"
        f"?uid={uid}&token={token}")
    queue = django_rq.get_queue('default')
    queue.enqueue(
        _send_html_email, 'Confirm your email', 'emails/activation_email.html',
        {'activation_link': activation_link, 'user_email': user.email},
        user.email,)


def send_password_confirm(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = (
        f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html"
        f"?uid={uid}&token={token}")
    queue = django_rq.get_queue('default')
    queue.enqueue(_send_html_email, 'Reset your Password',
                  'emails/password_reset_email.html',
                  {'reset_link': reset_link}, user.email,)
