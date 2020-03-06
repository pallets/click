from functools import update_wrapper

from PIL import Image
from PIL import ImageEnhance
from PIL import ImageFilter

import click


@click.group(chain=True)
def cli():
    """This script processes a bunch of images through pillow in a unix
    pipe.  One commands feeds into the next.

    Example:

    \b
        imagepipe open -i example01.jpg resize -w 128 display
        imagepipe open -i example02.jpg blur save
    """


@cli.resultcallback()
def process_commands(processors):
    """This result callback is invoked with an iterable of all the chained
    subcommands.  As in this example each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)

    # Evaluate the stream and throw away the items.
    for _ in stream:
        pass


def processor(f):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """

    def new_func(*args, **kwargs):
        def processor(stream):
            return f(stream, *args, **kwargs)

        return processor

    return update_wrapper(new_func, f)


def generator(f):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter.
    """

    @processor
    def new_func(stream, *args, **kwargs):
        for item in stream:
            yield item
        for item in f(*args, **kwargs):
            yield item

    return update_wrapper(new_func, f)


def copy_filename(new, old):
    new.filename = old.filename
    return new


@cli.command("open")
@click.option(
    "-i",
    "--image",
    "images",
    type=click.Path(),
    multiple=True,
    help="The image file to open.",
)
@generator
def open_cmd(images):
    """Loads one or multiple images for processing.  The input parameter
    can be specified multiple times to load more than one image.
    """
    for image in images:
        try:
            click.echo('Opening "%s"' % image)
            if image == "-":
                img = Image.open(click.get_binary_stdin())
                img.filename = "-"
            else:
                img = Image.open(image)
            yield img
        except Exception as e:
            click.echo('Could not open image "%s": %s' % (image, e), err=True)


@cli.command("save")
@click.option(
    "--filename",
    default="processed-%04d.png",
    type=click.Path(),
    help="The format for the filename.",
    show_default=True,
)
@processor
def save_cmd(images, filename):
    """Saves all processed images to a series of files."""
    for idx, image in enumerate(images):
        try:
            fn = filename % (idx + 1)
            click.echo('Saving "%s" as "%s"' % (image.filename, fn))
            yield image.save(fn)
        except Exception as e:
            click.echo('Could not save image "%s": %s' % (image.filename, e), err=True)


@cli.command("display")
@processor
def display_cmd(images):
    """Opens all images in an image viewer."""
    for image in images:
        click.echo('Displaying "%s"' % image.filename)
        image.show()
        yield image


@cli.command("resize")
@click.option("-w", "--width", type=int, help="The new width of the image.")
@click.option("-h", "--height", type=int, help="The new height of the image.")
@processor
def resize_cmd(images, width, height):
    """Resizes an image by fitting it into the box without changing
    the aspect ratio.
    """
    for image in images:
        w, h = (width or image.size[0], height or image.size[1])
        click.echo('Resizing "%s" to %dx%d' % (image.filename, w, h))
        image.thumbnail((w, h))
        yield image


@cli.command("crop")
@click.option(
    "-b", "--border", type=int, help="Crop the image from all sides by this amount."
)
@processor
def crop_cmd(images, border):
    """Crops an image from all edges."""
    for image in images:
        box = [0, 0, image.size[0], image.size[1]]

        if border is not None:
            for idx, val in enumerate(box):
                box[idx] = max(0, val - border)
            click.echo('Cropping "%s" by %dpx' % (image.filename, border))
            yield copy_filename(image.crop(box), image)
        else:
            yield image


def convert_rotation(ctx, param, value):
    if value is None:
        return
    value = value.lower()
    if value in ("90", "r", "right"):
        return (Image.ROTATE_90, 90)
    if value in ("180", "-180"):
        return (Image.ROTATE_180, 180)
    if value in ("-90", "270", "l", "left"):
        return (Image.ROTATE_270, 270)
    raise click.BadParameter('invalid rotation "%s"' % value)


def convert_flip(ctx, param, value):
    if value is None:
        return
    value = value.lower()
    if value in ("lr", "leftright"):
        return (Image.FLIP_LEFT_RIGHT, "left to right")
    if value in ("tb", "topbottom", "upsidedown", "ud"):
        return (Image.FLIP_LEFT_RIGHT, "top to bottom")
    raise click.BadParameter('invalid flip "%s"' % value)


@cli.command("transpose")
@click.option(
    "-r", "--rotate", callback=convert_rotation, help="Rotates the image (in degrees)"
)
@click.option("-f", "--flip", callback=convert_flip, help="Flips the image  [LR / TB]")
@processor
def transpose_cmd(images, rotate, flip):
    """Transposes an image by either rotating or flipping it."""
    for image in images:
        if rotate is not None:
            mode, degrees = rotate
            click.echo('Rotate "%s" by %ddeg' % (image.filename, degrees))
            image = copy_filename(image.transpose(mode), image)
        if flip is not None:
            mode, direction = flip
            click.echo('Flip "%s" %s' % (image.filename, direction))
            image = copy_filename(image.transpose(mode), image)
        yield image


@cli.command("blur")
@click.option("-r", "--radius", default=2, show_default=True, help="The blur radius.")
@processor
def blur_cmd(images, radius):
    """Applies gaussian blur."""
    blur = ImageFilter.GaussianBlur(radius)
    for image in images:
        click.echo('Blurring "%s" by %dpx' % (image.filename, radius))
        yield copy_filename(image.filter(blur), image)


@cli.command("smoothen")
@click.option(
    "-i",
    "--iterations",
    default=1,
    show_default=True,
    help="How many iterations of the smoothen filter to run.",
)
@processor
def smoothen_cmd(images, iterations):
    """Applies a smoothening filter."""
    for image in images:
        click.echo(
            'Smoothening "%s" %d time%s'
            % (image.filename, iterations, iterations != 1 and "s" or "",)
        )
        for _ in range(iterations):
            image = copy_filename(image.filter(ImageFilter.BLUR), image)
        yield image


@cli.command("emboss")
@processor
def emboss_cmd(images):
    """Embosses an image."""
    for image in images:
        click.echo('Embossing "%s"' % image.filename)
        yield copy_filename(image.filter(ImageFilter.EMBOSS), image)


@cli.command("sharpen")
@click.option(
    "-f", "--factor", default=2.0, help="Sharpens the image.", show_default=True
)
@processor
def sharpen_cmd(images, factor):
    """Sharpens an image."""
    for image in images:
        click.echo('Sharpen "%s" by %f' % (image.filename, factor))
        enhancer = ImageEnhance.Sharpness(image)
        yield copy_filename(enhancer.enhance(max(1.0, factor)), image)


@cli.command("paste")
@click.option("-l", "--left", default=0, help="Offset from left.")
@click.option("-r", "--right", default=0, help="Offset from right.")
@processor
def paste_cmd(images, left, right):
    """Pastes the second image on the first image and leaves the rest
    unchanged.
    """
    imageiter = iter(images)
    image = next(imageiter, None)
    to_paste = next(imageiter, None)

    if to_paste is None:
        if image is not None:
            yield image
        return

    click.echo('Paste "%s" on "%s"' % (to_paste.filename, image.filename))
    mask = None
    if to_paste.mode == "RGBA" or "transparency" in to_paste.info:
        mask = to_paste
    image.paste(to_paste, (left, right), mask)
    image.filename += "+" + to_paste.filename
    yield image

    for image in imageiter:
        yield image
