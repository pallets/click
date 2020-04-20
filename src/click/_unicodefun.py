import codecs
import os


def _verify_python3_env():
    """Ensures that the environment is good for unicode on Python 3."""
    try:
        import locale

        fs_enc = codecs.lookup(locale.getpreferredencoding()).name
    except Exception:
        fs_enc = "ascii"
    if fs_enc != "ascii":
        return

    extra = ""
    if os.name == "posix":
        import subprocess

        try:
            rv = subprocess.Popen(
                ["locale", "-a"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ).communicate()[0]
        except OSError:
            rv = b""
        good_locales = set()
        has_c_utf8 = False

        # Make sure we're operating on text here.
        if isinstance(rv, bytes):
            rv = rv.decode("ascii", "replace")

        for line in rv.splitlines():
            locale = line.strip()
            if locale.lower().endswith((".utf-8", ".utf8")):
                good_locales.add(locale)
                if locale.lower() in ("c.utf8", "c.utf-8"):
                    has_c_utf8 = True

        extra += "\n\n"
        if not good_locales:
            extra += (
                "Additional information: on this system no suitable"
                " UTF-8 locales were discovered. This most likely"
                " requires resolving by reconfiguring the locale"
                " system."
            )
        elif has_c_utf8:
            extra += (
                "This system supports the C.UTF-8 locale which is"
                " recommended. You might be able to resolve your issue"
                " by exporting the following environment variables:\n\n"
                "    export LC_ALL=C.UTF-8\n"
                "    export LANG=C.UTF-8"
            )
        else:
            extra += (
                "This system lists a couple of UTF-8 supporting locales"
                " that you can pick from. The following suitable"
                " locales were discovered: {}".format(", ".join(sorted(good_locales)))
            )

        bad_locale = None
        for locale in os.environ.get("LC_ALL"), os.environ.get("LANG"):
            if locale and locale.lower().endswith((".utf-8", ".utf8")):
                bad_locale = locale
            if locale is not None:
                break
        if bad_locale is not None:
            extra += (
                "\n\nClick discovered that you exported a UTF-8 locale"
                " but the locale system could not pick up from it"
                " because it does not exist. The exported locale is"
                " '{}' but it is not supported".format(bad_locale)
            )

    raise RuntimeError(
        "Click will abort further execution because Python 3 was"
        " configured to use ASCII as encoding for the environment."
        " Consult https://click.palletsprojects.com/python3/ for"
        " mitigation steps.{}".format(extra)
    )
