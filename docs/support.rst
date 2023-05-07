.. _support:

=======================
Support and Stability
=======================

Click is a mature projects with many uses in production, as such it prioritizes backward capability and stability. For feature requests that fall outside that core project see :ref:`click-contrib-heading`.

.. _click-contrib-heading:

click-contrib
---------------------

As the userbase of Click grows, more and more major feature requests pop up in
Click's bugtracker. As reasonable as it may be for those features to be bundled
with Click instead of being a standalone project, many of those requested
features are either highly experimental or have unproven practical use, while
potentially being a burden to maintain.

This is why click-contrib_ exists. The GitHub organization is a collection of
possibly experimental third-party packages whose featureset does not belong
into Click, but also a playground for major features that may be added to Click
in the future. It is also meant to coordinate and concentrate effort on writing
third-party extensions for Click, and to ease the effort of searching for such
extensions. In that sense it could be described as a low-maintenance
alternative to extension repositories of other frameworks.

Please note that the quality and stability of those packages may be different
than what you expect from Click itself. While published under a common
organization, they are still projects separate from Click.

Python Version Support
--------------------------
Click supports `the same versions as python <https://devguide.python.org/versions/>`_. Currently, Click supports Python >= 3.7.

Currently, no fixes are backported to earlier versions.

.. _click-contrib: https://github.com/click-contrib/
