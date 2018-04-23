# $ click_

[![Build status](https://ci.appveyor.com/api/projects/status/pjxh5g91jpbh7t84?svg=true)](https://ci.appveyor.com/project/tygerbytes/resourcefitness) 

## What's Click? 

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary.  It's the "Command
Line Interface Creation Kit".  It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing any frustration caused by the inability to implement
an intended CLI API.

Click in three points:
 -   arbitrary nesting of commands
 -   automatic help page generation
 -   supports lazy loading of subcommands at runtime
 
## Example 
What does it look like? Here is an example of a simple Click program:
```python
import click

@click.command()
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name',
              help='The person to greet.')
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        click.echo('Hello %s!' % name)

if __name__ == '__main__':
    hello()
```
And what it looks like when run:
```shell
$ python hello.py --count=3
Your name: John
Hello John!
Hello John!
Hello John!
```

## Installation
The installation process is easy and contained.
```
$ pip install Click
```
Or you can build from source.
```
$ git clone https://github.com/pallets/click.git
$ python setup.py install 
```
 
## Documentation

Read the docs at http://click.pocoo.org/

## Status

This library is stable and active. Feedback is always welcome!
