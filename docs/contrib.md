(contrib)=

# click-contrib

As the number of users of Click grows, more and more major feature requests are made. To users it may seem reasonable to
include those features with Click; however, many of them are experimental or aren't practical to support generically.
Maintainers have to choose what is reasonable to maintain in Click core.

The [click-contrib] GitHub organization exists as a place to collect third-party packages that extend Click's features.
It is also meant to ease the effort of searching for such extensions.

Please note that the quality and stability of those packages may be different than Click itself. While published under a
common organization, they are still separate from Click and the Pallets maintainers.

## Third-party projects

Other projects that extend Click's features are available outside of the [click-contrib] organization.

Some of the most popular and actively maintained are listed below:
| Project                                   | Description                                                                                               | Popularity                                                                                                              | Activity                                                                                                               |
|-------------------------------------------|-----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| [Typer](https://github.com/fastapi/typer) | Use Python type hints to create CLI apps.                                                                 | ![GitHub stars](https://img.shields.io/github/stars/fastapi/typer?label=%20&style=flat-square)                          | ![Last commit](https://img.shields.io/github/last-commit/fastapi/typer?label=%20&style=flat-square)                    |
| [rich-click](https://github.com/ewels/rich-click)       | Format help output with Rich.                                                        | ![GitHub stars](https://img.shields.io/github/stars/ewels/rich-click?label=%20&style=flat-square)                       | ![Last commit](https://img.shields.io/github/last-commit/ewels/rich-click?label=%20&style=flat-square)                 |
| [click-app](https://github.com/simonw/click-app)        | Cookiecutter template for creating new CLIs.                                            | ![GitHub stars](https://img.shields.io/github/stars/simonw/click-app?label=%20&style=flat-square)                       | ![Last commit](https://img.shields.io/github/last-commit/simonw/click-app?label=%20&style=flat-square)                  |
| [Cloup](https://github.com/janluke/cloup)               | Adds option groups, constraints, command aliases, help themes, suggestions and more.        | ![GitHub stars](https://img.shields.io/github/stars/janluke/cloup?label=%20&style=flat-square)                           | ![Last commit](https://img.shields.io/github/last-commit/janluke/cloup?label=%20&style=flat-square)                     |
| [Click Extra](https://github.com/kdeldycke/click-extra) | Cloup + colorful `--help`, `--config`, `--show-params`, `--verbosity` options, etc.           | ![GitHub stars](https://img.shields.io/github/stars/kdeldycke/click-extra?label=%20&style=flat-square)                   | ![Last commit](https://img.shields.io/github/last-commit/kdeldycke/click-extra?label=%20&style=flat-square)             |


:::{note}
To make it into the list above, a project:

- must be actively maintained (at least one commit in the last year)
- must have a reasonable number of stars (at least 20)

If you have a project that meets these criteria, please open a pull request
to add it to the list.

If a project is no longer maintained or does not meet the criteria above,
please open a pull request to remove it from the list.
:::

[click-contrib]: https://github.com/click-contrib/

