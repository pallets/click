(kwarg-refence)=

# Options and Arguments KeyWord Reference

```{contents}
:depth: 2
:local: true
```

The table answers the question, is the keyword argument (kwarg) expressive.
Along the top is situations. Right now some are just kwargs hopefully they all
get proper names.

## Options inherited from Parameter

```{table}
:align: center

| Kwarg          | single arg | nargs >= 2  | multiple    | counting   | boolean           | flag value   | ?   |
| ---------------| ---------- | ----------- |-------------|------------|-------------------|--------------|-----|
| type           | Yes        | Yes, Note 1 | Yes, Note 1 | No, Note 2 | No, Note 3        | Yes          |     |
| required       | Yes        | Yes         | Yes         | Yes        | Sometimes, Note 6 | No           |     |
| default        | Yes        | Yes, Note 4 | Yes, Note 4 | Yes        | Yes               | Yes, Note 5  |     |
| callback       | Yes        | Yes         | Yes         | Yes, Note 7| Yes, Note 7       | Yes, Note 7  |     |
| nargs          | Defines    | Defines     | Yes         | No, Note 9 | No, Note 10       | Yes, Note 11 |     |
| metavar        | Yes        | Yes         | Yes         | Yes        | Yes               | Yes          |     |
| expose_value   | Yes        | Yes         | Yes         | Yes        | Yes               | Yes          |     |
| is_eager       | Yes        | Yes         | Yes         | Yes        | Yes               | Yes          |     |
| envvar         | Yes        | Yes         | Yes         | Yes        | Yes               | Yes          |     |
| shell complete | Yes        | Yes         | Yes         | Yes        | Yes               | Yes          |     |
| deprecated     | Yes        | Yes         | Yes         | Yes        | No                | Yes          |     |
| multiple       | Yes        | Yes         | Defines     | No         | No                | No           |     |
```


Notes:
1. Specify the type of arg not them as group
1. The type is set implicitly, and there is only 1 right value, int. NW.
3. The type is set implicitly, and there is only 1 right value, bool. NW.
1. The value must have arity equal to args value.
1. In addition to normal usage, default may be used to indicate which of the flag values is default, by `default = True`.
6. In the simple `is_flag=True`, no. In the `--flag/--no-flag`, yes indicating you must select one.
1. Only use case (that I can think of) is multiple parameter dependent validation
1. The type is set implicitly, and there is only 1 right value, 1
9. Breaks but produces a weird error.
1. Breaks but produces a weird error.
1. Works, but I think not in the expected way

Abbreviations:
* NW: No warn. Click does not stop you.
* Defines: Sets situation


Terms:
* [arity](https://en.wikipedia.org/wiki/Arity)


Note 1:
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', nargs=2, type=str)
    def echo(echoes):
        click.echo(echoes)


.. click:run::

    invoke(echo, args=['--echoes', '2', '2'])
```

Note 4:
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', nargs=2, default=('p', 'y'))
    def echo(echoes):
        click.echo(echoes)


.. click:run::

    invoke(echo, args=['--echoes', '2', '2'])
```

Note 9
nargs x counting
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', nargs=2, count=True)
    def echo(echoes):
        click.echo(echoes)

.. click:run::
    invoke(echo, args=['--echoes', '1', '2'])
```

Note 10
nargs x boolean
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', nargs=2, is_flag=True)
    def echo(echoes):
        click.echo(echoes)

.. click:run::
    invoke(echo, args=['--echoes', '1', '2'])
```

Note 11
nargs x boolean
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', nargs=2, flag_value=(True, True))
    def echo(echoes):
        click.echo(echoes)

.. click:run::
    invoke(echo, args=['--echoes', ])
```

type x multiple
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', multiple=True)
    def echo(echoes):
        click.echo(echoes)

.. click:run::

    invoke(echo, args=['--echoes', '2', '--echoes', '2'])
```

type x counting
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', count=True,)
    def echo(echoes):
        click.echo(echoes)

.. click:run::

    invoke(echo, args=['--echoes', '--echoes', ])
```

type x boolean
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', is_flag=True, type=int)
    def echo(echoes):
        click.echo(echoes)

.. click:run::

    invoke(echo, args=['--echoes'])
```

default x counting
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', count=True, default=2)
    def echo(echoes):
        click.echo(echoes)

.. click:run::

    invoke(echo, args=[ ])
```

required x boolean
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes/--no-echoes', is_flag=True, required=True, )
    def echo(echoes):
        click.echo(echoes)

.. click:run::

    invoke(echo, args=['--no-echoes'])
```

required x flag value
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--present', 'echoes', is_flag=True, flag_value='present', required=True)
    @click.option('--past', 'echoes', is_flag=True, flag_value='past')
    def echo(echoes):
        click.echo(echoes)

.. click:run::

    invoke(echo, args=[])
```

callback x counting
```{eval-rst}
.. click:example::

    def validate_count(ctx, param, value):
        print(f"validation: {value}" )
        return value

    @click.command()
    @click.option('--echoes', count=True, callback=validate_count)
    def echo(echoes):
        click.echo(echoes)

.. click:run::

    invoke(echo, args=[ '--echoes'])
```

metavar x nargs >= 2
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', nargs=2,)
    def echo(echoes):
        click.echo(echoes)

.. click:run::
    invoke(echo, args=['--help', ])
```

metavar x multiple
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echoes', multiple=True, metavar='meta')
    def echo(echoes):
        click.echo(echoes)

.. click:run::
    invoke(echo, args=['--help', ])
    invoke(echo, args=['--echoes', '2', '--echoes', '2'])
```

## Options from class

```{table}
:align: center

| Kwarg | basic | multi value | multiple | counting |
| ----- | ----- | ----------- |----------|----------|
| default | Yes | Note        | ?        |          |
```

## Arguments inherited from Parameter

```{table}
:align: center

| Kwarg          | single arg | nargs >= 2  | nargs == -1 | Placeholder| Placeholder       |
| ---------------| ---------- | ----------- |-------------|------------|-------------------|
| type           | Yes        | Yes,        | Yes         | -          | -                 |
| required       | Yes        | Yes         | Yes         | -          | -                 |
| default        | Yes        | Yes         | Yes         | -          | -                 |
| callback       | Yes        | Yes         | Yes         | -          | -                 |
| nargs          | Defines    | Defines     | Defines     | -          | -                 |
| metavar        | Yes        | Yes         | Yes         | -          | -                 |
| expose_value   | Yes        | Yes         | Yes         | -          | -                 |
| is_eager       | No         | No          | No          | -          | -                 |
| envvar         | Yes        | Yes         | Yes         | -          | -                 |
| shell complete | Yes        | Yes         | Yes         | -          | -                 |
| deprecated     | Yes        | Yes         | Yes         | -          | -                 |
| multiple       | No         | No          | No          | -          | -                 |
```
