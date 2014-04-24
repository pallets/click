#!/usr/bin/python
#
# Generate passwords like Randall Munroe (http://xkcd.com/936/)
# Default dictionary from http://www.englishclub.com/vocabulary/common-words-5000.htm
#
import random
import click


@click.command()
@click.option('--length', default=4, help='Specify the password length', type=click.INT)
@click.option('--dictionary', default="dictionary", help='Specify a path to a dictionary', type=click.File())
def generate_password(dictionary, length):
    if type(dictionary) != file:
        dictionary = open(dictionary, "r")
    print " ".join(map(str.strip, random.sample(dictionary.readlines(), length)))

if __name__ == "__main__":
    generate_password()
