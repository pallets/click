import os
import typing as t
from gettext import NullTranslations
from gettext import translation as build_translations_object

_translations: NullTranslations = NullTranslations()
_active_locale: t.Union[str, None] = None


LOCALE_ROOT_PATH = os.path.join(os.path.dirname(__file__), "locales")


def reset_click_locale() -> None:
    """Reset the active locale."""

    global _active_locale
    global _translations
    _active_locale = None
    _translations = NullTranslations()


def set_click_locale(target_locale: str) -> None:
    """Set the locale. If the locale is unrecognized, a NotImplementedError is raised.

    :param target_locale: The name of the locale, e.g. en_US
    """
    global _active_locale
    global _translations

    try:
        _translations = build_translations_object(
            "click", LOCALE_ROOT_PATH, [target_locale]
        )
    except FileNotFoundError:
        raise NotImplementedError(f"Unrecognized locale {target_locale}") from None
    else:
        _active_locale = target_locale


def get_click_locale() -> t.Union[str, None]:
    """Get the active locale."""
    return _active_locale


def gettext(message: str) -> str:
    """Wrapper around the gettext.gettext function that respects click's active locale.

    :param message: The message id to translate.
    """
    return _translations.gettext(message)


def ngettext(msgid1: str, msgid2: str, n: int) -> str:
    """Wrapper around the gettext.ngettext function that respects click's active locale.

    :param msgid1: Singular form of the message id.
    :param msgid2: Plural form of the message id.
    :n: The number used to determine the form.
    """
    return _translations.ngettext(msgid1, msgid2, n)
