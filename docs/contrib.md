(contrib)=

# Related projects

As the user number of Click grows, more and more major feature requests are
made. To users, it may seem reasonable to include those features with Click;
however, many of them are experimental or aren't practical to support
generically. Maintainers have to choose what is reasonable to maintain in Click
core.

Please note that the quality and stability of the projects below may be different from
Click itself. They are separate from Click and the Pallets maintainers.

## `click-contrib`

The [`click-contrib`](https://github.com/click-contrib/) GitHub organization exists as a
place to collect third-party packages that extend Click's features. It is also meant to
ease the effort of searching for such extensions.

| Project                                                         | Description                                | Popularity                                                                                                   | Activity                                                                                                          |
|-----------------------------------------------------------------|--------------------------------------------|--------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| [click-spinner](https://github.com/click-contrib/click-spinner) | Show a spinner while a command runs.       | ![GitHub stars](https://img.shields.io/github/stars/click-contrib/click-spinner?label=%20&style=flat-square) | ![Last commit](https://img.shields.io/github/last-commit/click-contrib/click-spinner?label=%20&style=flat-square) |
| [click-repl](https://github.com/click-contrib/click-repl)       | Run subcommands in a REPL.                 | ![GitHub stars](https://img.shields.io/github/stars/click-contrib/click-repl?label=%20&style=flat-square)    | ![Last commit](https://img.shields.io/github/last-commit/click-contrib/click-repl?label=%20&style=flat-square)    |
| [sphinx-click](https://github.com/click-contrib/sphinx-click)   | Document Click applications with Sphinx.   | ![GitHub stars](https://img.shields.io/github/stars/click-contrib/sphinx-click?label=%20&style=flat-square)  | ![Last commit](https://img.shields.io/github/last-commit/click-contrib/sphinx-click?label=%20&style=flat-square)  |
| [click-man](https://github.com/click-contrib/click-man)         | Generate man pages for Click applications. | ![GitHub stars](https://img.shields.io/github/stars/click-contrib/click-man?label=%20&style=flat-square)     | ![Last commit](https://img.shields.io/github/last-commit/click-contrib/click-man?label=%20&style=flat-square)     |
| [click-plugins](https://github.com/click-contrib/click-plugins) | Register commands through entry points.    | ![GitHub stars](https://img.shields.io/github/stars/click-contrib/click-plugins?label=%20&style=flat-square) | ![Last commit](https://img.shields.io/github/last-commit/click-contrib/click-plugins?label=%20&style=flat-square) |
| [click-aliases](https://github.com/click-contrib/click-aliases) | Add aliases to commands.                   | ![GitHub stars](https://img.shields.io/github/stars/click-contrib/click-aliases?label=%20&style=flat-square) | ![Last commit](https://img.shields.io/github/last-commit/click-contrib/click-aliases?label=%20&style=flat-square) |

## Third-party projects

Other projects that extend Click are available. Here are some of the most popular and
actively maintained ones:

| Project                                                 | Description                                                                          | Popularity                                                                                             | Activity                                                                                                    |
|---------------------------------------------------------|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| [tqdm](https://github.com/tqdm/tqdm)                    | Fast, extensible progress bars.                                                      | ![GitHub stars](https://img.shields.io/github/stars/tqdm/tqdm?label=%20&style=flat-square)             | ![Last commit](https://img.shields.io/github/last-commit/tqdm/tqdm?label=%20&style=flat-square)             |
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
- must have a reasonable number of stars (at least 50)

If you have a project that meets these criteria, please open a pull request
to add it to the list.

If a project is no longer maintained or does not meet the criteria above,
please open a pull request to remove it from the list.
```
