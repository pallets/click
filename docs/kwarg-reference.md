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

| Kwarg    | basic | nargs >= 2  | multiple    | counting   | boolean           | flag value   | ?   |
| ---------| ----- | ----------- |-------------|------------|-------------------|--------------|-----|
| type     | Yes   | Yes, Note 1 | Yes, Note 1 | No, Note 2 | No, Note 3        | Yes          |     |
| default  | Yes   | Yes, Note 4 | Yes, Note 4 | Yes        | Yes               | Yes, Note 5  |     |
| required | Yes   | Yes         | Yes         | Yes        | Sometimes, Note 6 | No           |     |
| callback | Yes   | Yes         | Yes         | Yes, Note 7| Yes, Note 7       | Yes, Note 7  |     |
| nargs    | -     | -           | -           | -          | -                 | -            |     |
| metavar  | Yes   | Yes         | Yes         | Yes        | Yes               | Yes          |     |
| expose_value | -     | -           | -           | -          | -                 | -            |     |
| nargs    | -     | -           | -           | -          | -                 | -            |     |


```


Notes:
1. Specify the type of arg not them as group
1. The type is set implicitly, and there is only 1 right value, int. NW.
3. The type is set implicitly, and there is only 1 right value, bool. NW.
1. The value must have arity equal to args value.
1. In addition to normal usage, default may be used to indicate which of the flag values is default, by `default = True`.
6. In the simple `is_flag=True`, no. In the `--flag/--no-flag`, yes indicating you must select one.
1. Only use case (that I can think of) is multiple parameter dependent validation

Abbreviations:
* NW: No warn. Click does not stop you.


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

| Kwarg | basic | multi value | multiple | counting |
| ----- | ----- | ----------- |----------|----------|
| default | Yes | Note        | ?        |          |
| type | ?   |             |          |          |
```

## Arguments from class

```{table}
:align: center

| Kwarg | basic | multi value | multiple | counting |
| ----- | ----- | ----------- |----------|----------|
| default | Yes | Note        | ?        |          |
```
