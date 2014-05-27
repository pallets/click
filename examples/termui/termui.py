# coding: utf-8
import click
import time
import random

try:
    range_type = xrange
except NameError:
    range_type = range


@click.group()
def cli():
    """This script showcases different terminal UI helpers in Click."""
    pass


@cli.command()
def colordemo():
    """Demonstrates ANSI color support."""
    for color in 'red', 'green', 'blue':
        click.echo(click.style('I am colored %s' % color, fg=color))
        click.echo(click.style('I am background colored %s' % color, bg=color))


@cli.command()
def pager():
    """Demonstrates using the pager."""
    lines = []
    for x in xrange(200):
        lines.append('%s. Hello World!' % click.style(str(x), fg='green'))
    click.echo_via_pager('\n'.join(lines))


@cli.command()
@click.option('--count', default=8000, type=click.IntRange(1, 100000),
              help='The number of items to process.')
def progress(count):
    """Demonstrates the progress bar."""
    items = range_type(count)

    def process_slowly(item):
        time.sleep(0.002 * random.random())

    def filter(items):
        for item in items:
            if random.random() > 0.3:
                yield item

    with click.progressbar(items, label='Processing user accounts',
                           fill_char=click.style('#', fg='green')) as bar:
        for item in bar:
            process_slowly(item)

    def show_item(item):
        if item is not None:
            return 'Item #%d' % item

    with click.progressbar(filter(items), label='Committing transaction',
                           fill_char=click.style('#', fg='yellow'),
                           item_show_func=show_item) as bar:
        for item in bar:
            process_slowly(item)

    with click.progressbar(length=count, label='Counting',
                           bar_template='%(label)s  %(bar)s | %(info)s',
                           fill_char=click.style(u'█', fg='cyan'),
                           empty_char=' ') as bar:
        for item in bar:
            process_slowly(item)


@cli.command()
def clear():
    """Clears the entire screen."""
    click.clear()
