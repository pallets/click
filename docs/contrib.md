(contrib)=

# click-contrib

As the user number of Click grows, more and more major feature requests are
made. To users, it may seem reasonable to include those features with Click;
however, many of them are experimental or aren't practical to support
generically. Maintainers have to choose what is reasonable to maintain in Click
core.

The [click-contrib](https://github.com/click-contrib/) GitHub organization exists as a place to collect third-party
packages that extend Click's features. It is also meant to ease the effort of
searching for such extensions.

Please note that the quality and stability of those packages may be different
from Click itself. While published under a common organization, they are still
separate from Click and the Pallets maintainers.

## Third-party projects

Other projects that extend Click's features are available outside the
[click-contrib](https://github.com/click-contrib/) organization.

Some of the most popular and actively maintained are listed below:

| Project                                                 | Description                                                                          | Popularity                                                                                             | Activity                                                                                                    |
|---------------------------------------------------------|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| [Typer](https://github.com/fastapi/typer)               | Use Python type hints to create CLI apps.                                            | ![GitHub stars](https://img.shields.io/github/stars/fastapi/typer?label=%20&style=flat-square)         | ![Last commit](https://img.shields.io/github/last-commit/fastapi/typer?label=%20&style=flat-square)         |
| [rich-click](https://github.com/ewels/rich-click)       | Format help output with Rich.                                                        | ![GitHub stars](https://img.shields.io/github/stars/ewels/rich-click?label=%20&style=flat-square)      | ![Last commit](https://img.shields.io/github/last-commit/ewels/rich-click?label=%20&style=flat-square)      |
| [shtab](https://github.com/tqdm/shtab)                  | Speed up tab completion scripts and support more shells.                             | ![GitHub stars](https://img.shields.io/github/stars/tqdm/shtab?label=%20&style=flat-square)            | ![Last commit](https://img.shields.io/github/last-commit/tqdm/shtab?label=%20&style=flat-square)            |
| [click-app](https://github.com/simonw/click-app)        | Cookiecutter template for creating new CLIs.                                         | ![GitHub stars](https://img.shields.io/github/stars/simonw/click-app?label=%20&style=flat-square)      | ![Last commit](https://img.shields.io/github/last-commit/simonw/click-app?label=%20&style=flat-square)      |
| [Cloup](https://github.com/janluke/cloup)               | Adds option groups, constraints, command aliases, help themes, suggestions and more. | ![GitHub stars](https://img.shields.io/github/stars/janluke/cloup?label=%20&style=flat-square)         | ![Last commit](https://img.shields.io/github/last-commit/janluke/cloup?label=%20&style=flat-square)         |
| [Click Extra](https://github.com/kdeldycke/click-extra) | Cloup + colorful `--help`, `--config`, `--show-params`, `--verbosity` options, etc.  | ![GitHub stars](https://img.shields.io/github/stars/kdeldycke/click-extra?label=%20&style=flat-square) | ![Last commit](https://img.shields.io/github/last-commit/kdeldycke/click-extra?label=%20&style=flat-square) |

## Interactive input libraries

Click reads a prompt with the built-in {func}`input` and embeds no line editor of its own. If you need fancy features like completion of arbitrary values, selection menus or fuzzy search you need to replace {func}`click.prompt` with a third-party library. The projects below are popular and actively maintained:

| Project                                                                   | Description                                                                | Popularity                                                                                                            | Activity                                                                                                                   |
|---------------------------------------------------------------------------|----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| [Textual](https://github.com/Textualize/textual)                          | Build terminal and web user interfaces with a Python API.                  | ![GitHub stars](https://img.shields.io/github/stars/Textualize/textual?label=%20&style=flat-square)                   | ![Last commit](https://img.shields.io/github/last-commit/Textualize/textual?label=%20&style=flat-square)                   |
| [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) | Build interactive command lines with completion, history and key bindings. | ![GitHub stars](https://img.shields.io/github/stars/prompt-toolkit/python-prompt-toolkit?label=%20&style=flat-square) | ![Last commit](https://img.shields.io/github/last-commit/prompt-toolkit/python-prompt-toolkit?label=%20&style=flat-square) |

```{note}
To make it into any of the lists above, a project:

- must be actively maintained (at least one commit in the last year)
- must have a reasonable number of stars (at least 20)

If you have a project that meets these criteria, please open a pull request
to add it to the list.

If a project is no longer maintained or does not meet the criteria above,
please open a pull request to remove it from the list.
```
