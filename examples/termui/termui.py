# coding: utf-8
import click
import math
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
    for x in range_type(200):
        lines.append('%s. Hello World!' % click.style(str(x), fg='green'))
    click.echo_via_pager('\n'.join(lines))


@cli.command()
def spinner():
    """Demonstrates using the spinner."""
    def do_work():
        time.sleep(3)

    click.echo('starting work')
    with click.spinner():
        do_work()
    click.echo('all done!')


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

    with click.progressbar(items, label='Processing accounts',
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

    with click.progressbar(length=count, width=0, show_percent=False,
                           show_eta=False,
                           fill_char=click.style('#', fg='magenta')) as bar:
        for item in bar:
            process_slowly(item)

    # 'Non-linear progress bar'
    steps = [math.exp( x * 1. / 20) - 1 for x in range(20)]
    count = int(sum(steps))
    with click.progressbar(length=count, show_percent=False,
                           label='Slowing progress bar',
                           fill_char=click.style(u'█', fg='green')) as bar:
        for item in steps:
            time.sleep(item)
            bar.update(item)


@cli.command()
@click.argument('url')
def open(url):
    """Opens a file or URL In the default application."""
    click.launch(url)


@cli.command()
@click.argument('url')
def locate(url):
    """Opens a file or URL In the default application."""
    click.launch(url, locate=True)


@cli.command()
def edit():
    """Opens an editor with some text in it."""
    MARKER = '# Everything below is ignored\n'
    message = click.edit('\n\n' + MARKER)
    if message is not None:
        msg = message.split(MARKER, 1)[0].rstrip('\n')
        if not msg:
            click.echo('Empty message!')
        else:
            click.echo('Message:\n' + msg)
    else:
        click.echo('You did not enter anything!')


@cli.command()
def clear():
    """Clears the entire screen."""
    click.clear()


@cli.command()
def pause():
    """Waits for the user to press a button."""
    click.pause()


@cli.command()
def menu():
    """Shows a simple menu."""
    menu = 'main'
    while 1:
        if menu == 'main':
            click.echo('Main menu:')
            click.echo('  d: debug menu')
            click.echo('  q: quit')
            char = click.getchar()
            if char == 'd':
                menu = 'debug'
            elif char == 'q':
                menu = 'quit'
            else:
                click.echo('Invalid input')
        elif menu == 'debug':
            click.echo('Debug menu')
            click.echo('  b: back')
            char = click.getchar()
            if char == 'b':
                menu = 'main'
            else:
                click.echo('Invalid input')
        elif menu == 'quit':
            return
