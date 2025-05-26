(virtualenv-heading)=

# Virtualenv

## Why Use Virtualenv?

You should use [Virtualenv](https://virtualenv.pypa.io/en/latest/) because:

- It allows you to install multiple versions of the same dependency.
- If you have an operating system version of Python, it prevents you from changing its dependencies and potentially
  messing up your os.

## How to Use Virtualenv

Create your project folder, then a virtualenv within it:

```console
$ mkdir myproject
$ cd myproject
$ python3 -m venv .venv
```

Now, whenever you want to work on a project, you only have to activate the corresponding environment.


```{eval-rst}
.. tabs::

    .. group-tab:: OSX/Linux

        .. code-block:: text

            $ . .venv/bin/activate
            (venv) $

    .. group-tab:: Windows

        .. code-block:: text

            > .venv\scripts\activate
            (venv) >
```

You are now using your virtualenv (notice how the prompt of your shell has changed to show the active environment).

To install packages in the virtual environment:

```console
$ pip install click
```

And if you want to stop using the virtualenv, use the following command:

```console
$ deactivate
```

After doing this, the prompt of your shell should be as familiar as before.
