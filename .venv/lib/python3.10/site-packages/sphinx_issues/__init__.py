"""A Sphinx extension for linking to your project's issue tracker."""

import importlib.metadata
import re
from typing import Callable, Optional

from docutils import nodes, utils
from sphinx.config import Config
from sphinx.util.nodes import split_explicit_title

GITHUB_USER_RE = re.compile("^https://github.com/([^/]+)/([^/]+)/.*")


def _get_default_group_and_project(
    config: Config, uri_config_option: str
) -> Optional[tuple[str, str]]:
    """
    Get the default group/project or None if not set
    """
    old_config = getattr(config, "issues_github_path", None)
    new_config = getattr(config, "issues_default_group_project", None)

    if old_config and new_config:
        raise ValueError(
            "Both 'issues_github_path' and 'issues_default_group_project' are set, even"
            " though they define the same setting.  "
            "Please only define one of these."
        )
    group_and_project = new_config or old_config

    if group_and_project:
        assert isinstance(group_and_project, str)
        try:
            group, project = group_and_project.split("/", maxsplit=1)
            return group, project
        except ValueError as e:
            raise ValueError(
                "`issues_github_path` or `issues_default_group_project` needs to "
                "define a value in the form of `<group or user>/<project>` "
                f"but `{config}` was given."
            ) from e

    # If group and project was not set, we need to look for it within the github url
    # for backward compatibility
    if not group_and_project:
        uri = getattr(config, uri_config_option)
        if uri:
            match = GITHUB_USER_RE.match(uri)
            if match:
                return match.groups()[0], match.groups()[1]

    return None


def _get_placeholder(uri_config_option: str) -> str:
    """
    Get the placeholder from the uri_config_option
    """
    try:
        # i.e. issues_pr_uri -> pr
        return uri_config_option[:-4].split("_", maxsplit=1)[1]
    except IndexError:
        # issues_uri -> issue
        return uri_config_option[:-5]


def _get_uri_template(
    config: Config,
    uri_config_option: str,
) -> str:
    """
    Get a URL format template that can be filled with user information based
    on the given configuration

    The result always contains the following placeholder
      - n (the issue number, user, pull request, etc...)

    The result can contain the following other placeholders
      - group (same as user in github)
      - project

    Examples for possible results:

         - "https://github.com/{group}/{project}/issues/{n}"

         - "https://gitlab.company.com/{group}/{project}/{n}"

         - "https://fancy.issuetrack.com?group={group}&project={project}&issue={n}"

    Raises:
         - ValueError if the given uri contains an invalid placeholder
    """
    format_string = str(getattr(config, uri_config_option))
    placeholder = _get_placeholder(uri_config_option)

    result = format_string.replace(f"{{{placeholder}}}", "{n}")

    try:
        result.format(project="", group="", n="")
    except (NameError, KeyError) as e:
        raise ValueError(
            f"The `{uri_config_option}` option contains invalid placeholders. "
            f"Only {{group}}, {{projects}} and {{{placeholder}}} are allowed."
            f'Invalid format string: "{format_string}".'
        ) from e
    return result


def _get_uri(
    uri_config_option: str,
    config: Config,
    number: str,
    group_and_project: Optional[tuple[str, str]] = None,
) -> str:
    """
    Get a URI based on the given configuration and do some sanity checking
    """
    format_string = _get_uri_template(config, uri_config_option)

    url_vars = {"n": number}

    config_group_and_project = _get_default_group_and_project(config, uri_config_option)
    if group_and_project:
        # Group and Project defined by call
        if config_group_and_project:
            to_replace = "/".join(config_group_and_project)
            if to_replace in format_string:
                # Backward compatibility, replace default group/project
                # with {group}/{project}
                format_string = format_string.replace(to_replace, "{group}/{project}")
        (url_vars["group"], url_vars["project"]) = group_and_project
    elif config_group_and_project:
        # If not defined by call use the default if given
        (url_vars["group"], url_vars["project"]) = config_group_and_project

    try:
        return format_string.format(**url_vars)
    except (NameError, KeyError) as e:
        # The format string was checked before, that it contains no additional not
        # supported placeholders. So this occur
        raise ValueError(
            f"The `{uri_config_option}` format `{format_string}` requires a "
            f"group/project to be defined in `issues_default_group_project`."
        ) from e


def pypi_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """Sphinx role for linking to a PyPI on https://pypi.org/.

    Examples: ::

        :pypi:`sphinx-issues`

    """
    options = options or {}
    content = content or []
    has_explicit_title, title, target = split_explicit_title(text)

    target = utils.unescape(target).strip()
    title = utils.unescape(title).strip()
    ref = f"https://pypi.org/project/{target}"
    text = title if has_explicit_title else target
    link = nodes.reference(text=text, refuri=ref, **options)
    return [link], []


class IssueRole:
    # Symbols used to separate and issue/pull request/merge request etc
    # i.e
    #   - group/project#2323 for issues
    #   - group/project!1234 for merge requests (in gitlab)
    #   - group/project@adbc1234 for commits
    ELEMENT_SEPARATORS = "#@!"

    EXTERNAL_REPO_REGEX = re.compile(rf"^(\w+)/(.+)([{ELEMENT_SEPARATORS}])([\w]+)$")

    def __init__(
        self,
        config_prefix: str,
        pre_format_text: Callable[[Config, str], str] = None,
    ):
        self.uri_config = f"{config_prefix}_uri"
        self.separator_config = f"{config_prefix}_prefix"
        self.pre_format_text = pre_format_text or self.default_pre_format_text

    @staticmethod
    def default_pre_format_text(config: Config, text: str) -> str:
        return text

    def format_text(self, config: Config, issue_no: str) -> str:
        """
        Add supported separator in front of the issue or raise an error if invalid
        separator is given
        """
        separator = getattr(config, self.separator_config)
        if separator not in self.ELEMENT_SEPARATORS:
            raise ValueError(
                f"Option {self.separator_config} has to be one of "
                f"{', '.join(self.ELEMENT_SEPARATORS)}."
            )
        text = self.pre_format_text(config, issue_no.lstrip(self.ELEMENT_SEPARATORS))
        return f"{separator}{text}"

    def make_node(self, name: str, issue_no: str, config: Config, options=None):
        if issue_no in ("-", "0"):
            return None

        options = options or {}

        has_explicit_title, title, target = split_explicit_title(issue_no)

        if has_explicit_title:
            issue_no = str(target)

        repo_match = self.EXTERNAL_REPO_REGEX.match(issue_no)

        if repo_match:
            # External repo
            group, project, original_separator, issue_no = repo_match.groups()
            text = f"{group}/{project}{self.format_text(config, issue_no)}"
            ref = _get_uri(
                self.uri_config,
                config,
                issue_no,
                (group, project),
            )
        else:
            text = self.format_text(config, issue_no)
            ref = _get_uri(self.uri_config, config, issue_no)
        if has_explicit_title:
            return nodes.reference(text=title, refuri=ref, **options)
        else:
            return nodes.reference(text=text, refuri=ref, **options)

    def __call__(
        self, name, rawtext, text, lineno, inliner, options=None, content=None
    ):
        options = options or {}
        content = content or []
        issue_nos = [each.strip() for each in utils.unescape(text).split(",")]
        config = inliner.document.settings.env.app.config
        ret = []
        for i, issue_no in enumerate(issue_nos):
            node = self.make_node(name, issue_no, config, options=options)
            ret.append(node)
            if i != len(issue_nos) - 1:
                sep = nodes.raw(text=", ", format="html")
                ret.append(sep)
        return ret, []


"""Sphinx role for linking to an issue. Must have
`issues_uri` or `issues_default_group_project` configured in ``conf.py``.
Examples: ::
    :issue:`123`
    :issue:`42,45`
    :issue:`sloria/konch#123`
"""
issue_role = IssueRole(
    config_prefix="issues",
)

"""Sphinx role for linking to a pull request. Must have
`issues_pr_uri` or `issues_default_group_project` configured in ``conf.py``.
Examples: ::
    :pr:`123`
    :pr:`42,45`
    :pr:`sloria/konch#43`
"""
pr_role = IssueRole(
    config_prefix="issues_pr",
)


def format_commit_text(config, sha):
    return sha[:7]


"""Sphinx role for linking to a commit. Must have
`issues_commit_uri` or `issues_default_group_project` configured in ``conf.py``.
Examples: ::
    :commit:`123abc456def`
    :commit:`sloria/konch@123abc456def`
"""
commit_role = IssueRole(
    config_prefix="issues_commit",
    pre_format_text=format_commit_text,
)

"""Sphinx role for linking to a user profile. Defaults to linking to
GitHub profiles, but the profile URIS can be configured via the
``issues_user_uri`` config value.

Examples: ::

    :user:`sloria`

Anchor text also works: ::

    :user:`Steven Loria <sloria>`
"""
user_role = IssueRole(config_prefix="issues_user")


def setup(app):
    # Format template for issues URI
    # e.g. 'https://github.com/sloria/marshmallow/issues/{issue}
    app.add_config_value(
        "issues_uri",
        default="https://github.com/{group}/{project}/issues/{issue}",
        rebuild="html",
        types=[str],
    )
    app.add_config_value("issues_prefix", default="#", rebuild="html", types=[str])
    # Format template for PR URI
    # e.g. 'https://github.com/sloria/marshmallow/pull/{issue}
    app.add_config_value(
        "issues_pr_uri",
        default="https://github.com/{group}/{project}/pull/{pr}",
        rebuild="html",
        types=[str],
    )
    app.add_config_value("issues_pr_prefix", default="#", rebuild="html", types=[str])
    # Format template for commit URI
    # e.g. 'https://github.com/sloria/marshmallow/commits/{commit}
    app.add_config_value(
        "issues_commit_uri",
        default="https://github.com/{group}/{project}/commit/{commit}",
        rebuild="html",
        types=[str],
    )
    app.add_config_value(
        "issues_commit_prefix", default="@", rebuild="html", types=[str]
    )
    # There is no seperator config as a format_text function is given

    # Default User (Group)/Project eg. 'sloria/marshmallow'
    # Called github as the package was working with github only before
    app.add_config_value(
        "issues_github_path", default=None, rebuild="html", types=[str]
    )
    # Same as above but with new naming to reflect the new functionality
    # Only on of both can be set
    app.add_config_value(
        "issues_default_group_project", default=None, rebuild="html", types=[str]
    )
    # Format template for user profile URI
    # e.g. 'https://github.com/{user}'
    app.add_config_value(
        "issues_user_uri",
        # Default to sponsors URL.
        # GitHub will automatically redirect to profile
        # if Sponsors isn't set up.
        default="https://github.com/sponsors/{user}",
        rebuild="html",
        types=[str],
    )
    app.add_config_value("issues_user_prefix", default="@", rebuild="html", types=[str])
    app.add_role("issue", issue_role)
    app.add_role("pr", pr_role)
    app.add_role("user", user_role)
    app.add_role("commit", commit_role)
    app.add_role("pypi", pypi_role)
    return {
        "version": importlib.metadata.version("sphinx-issues"),
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
