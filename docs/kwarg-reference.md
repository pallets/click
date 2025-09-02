(kwarg-refence)=

# Options and Arguments KeyWord Reference

```{contents}
:depth: 2
:local: true
```

Answers the question, is the keyword argument (kwarg) expressive
N

## Options inherited from Parameter

```{table}
:align: center

| Kwarg    | basic | nargs >= 2  | multiple    | counting   | boolean    | flag value   | ?   |
| ---------| ----- | ----------- |-------------|------------|------------|--------------|-----|
| type     | Yes   | Yes, Note 1 | Yes, Note 1 | No, Note 2 | No, Note 3 |  Yes         |     |
| default  | Yes   | Yes, Note 4 | Yes, Note 4 | Yes        | Yes        |  Yes, Note 5? | |
| default  | Yes   | Note 1      | ?           |          |         |            | |

```


Notes:
1. Specify the type of arg not them as group
1. The type is set implicitly, and there is only 1 right value, int. NW.
1. The type is set implicitly, and there is only 1 right value, bool. NW.
4. The value must have arity equal to args value.

Abbreviations:
* NW: No warn. Click does not stop you.

Terms:
* [arity](https://en.wikipedia.org/wiki/Arity)


Note 1:
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echos', nargs=2, type=str)
    def echo(echos):
        click.echo(echos)


.. click:run::

    invoke(echo, args=['--echos', '2', '2'])
```

Note 4:
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echos', nargs=2, default=('p', 'y'))
    def echo(echos):
        click.echo(echos)


.. click:run::

    invoke(echo, args=['--echos', '2', '2'])
```

type x multiple
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echos', multiple=True)
    def echo(echos):
        click.echo(echos)

.. click:run::

    invoke(echo, args=['--echos', '2', '--echos', '2'])
```

type x counting
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echos', count=True,)
    def echo(echos):
        click.echo(echos)

.. click:run::

    invoke(echo, args=['--echos', '--echos', ])
```

type x boolean
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echos', is_flag=True, type=int)
    def echo(echos):
        click.echo(echos)

.. click:run::

    invoke(echo, args=['--echos'])
```

default x counting
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echos', count=True, default=2)
    def echo(echos):
        click.echo(echos)

.. click:run::

    invoke(echo, args=[ ])
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
