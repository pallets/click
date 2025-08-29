(kwarg-refence)=

# Options and Arguments KeyWord Reference

```{contents}
:depth: 2
:local: true
```

Answers the question, is the keyword argument (kwarg) applicable
N

## Options inherited from Parameter

```{table}
:align: center

| Kwarg    | basic | nargs >= 2  | multiple | counting | boolean | flag value | flag|
| ---------| ----- | ----------- |----------|----------|---------|------------|-----|
| type     | Yes   | Note 1      | Note 1   |No, NW    |         |            | |
| type     | ?     |             |          |          |         |            | |
| default  | Yes   | Note 1      | ?        |          |         |            | |

```
NW: No warn. Click does not stop you.
Note 1: Specify the type of arg not them as group
Note

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

type x multiple
```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--echos', multiple=True, type=str)
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
