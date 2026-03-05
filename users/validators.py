from rest_framework.exceptions import ValidationError


def is_only_letters(text):
    if not text.isalpha():
        raise ValidationError("Поле может содержать только буквы")
