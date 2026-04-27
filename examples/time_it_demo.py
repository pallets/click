import time

import click


def demo_writing_a():
    """写法 A：直接装饰命令函数

    @click.command()
    @click.time_it
    def cmd1(): pass
    """
    @click.command()
    @click.time_it
    def cmd1():
        click.echo("Running cmd1...")
        time.sleep(0.05)
        click.echo("cmd1 finished.")

    click.echo("\n" + "=" * 50)
    click.echo("写法 A：@click.command() 后接 @click.time_it")
    click.echo("=" * 50)
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cmd1, [])
    click.echo(result.output, nl=False)
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    return result.exit_code == 0


def demo_writing_b():
    """写法 B：带参数装饰命令函数

    @click.command()
    @click.time_it(name="custom")
    def cmd2(): pass
    """
    @click.command()
    @click.time_it(name="custom_timer")
    def cmd2():
        click.echo("Running cmd2...")
        time.sleep(0.05)
        click.echo("cmd2 finished.")

    click.echo("\n" + "=" * 50)
    click.echo("写法 B：@click.time_it(name=\"custom\")")
    click.echo("=" * 50)
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cmd2, [])
    click.echo(result.output, nl=False)
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    return result.exit_code == 0


def demo_writing_c():
    """写法 C：装饰已有 Command 对象

    @click.time_it
    @click.command()
    def cmd3(): pass

    注意：装饰器从下往上执行，所以 @click.command() 先执行，
    创建 Command 对象，然后 @click.time_it 装饰这个 Command 对象。
    """
    @click.time_it
    @click.command()
    def cmd3():
        click.echo("Running cmd3...")
        time.sleep(0.05)
        click.echo("cmd3 finished.")

    click.echo("\n" + "=" * 50)
    click.echo("写法 C：@click.time_it 后接 @click.command()")
    click.echo("=" * 50)
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cmd3, [])
    click.echo(result.output, nl=False)
    if result.exception:
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    return result.exit_code == 0


def demo_timer_context_manager():
    """演示 click.timer 上下文管理器的使用"""
    click.echo("\n" + "=" * 50)
    click.echo("演示 click.timer 上下文管理器")
    click.echo("=" * 50)

    click.echo("\n--- 演示 1: 基础 timer ---")
    with click.timer():
        time.sleep(0.05)

    click.echo("\n--- 演示 2: 带名称的 timer ---")
    with click.timer(name="my operation"):
        time.sleep(0.05)

    click.echo("\n--- 演示 3: 获取 elapsed 时间 ---")
    with click.timer() as tm:
        time.sleep(0.02)
        click.echo(f"During: elapsed = {tm.elapsed:.4f}s")
        time.sleep(0.02)
    click.echo(f"After: elapsed = {tm.elapsed:.4f}s")

    click.echo("\n--- 演示 4: 未 enter 时访问 elapsed 会抛出错误 ---")
    tm = click.timer()
    try:
        _ = tm.elapsed
    except RuntimeError as e:
        click.echo(f"Expected error: {e}")


@click.command()
@click.option("--all", "-a", is_flag=True, help="Run all demos")
@click.option("--a", "demo_a", is_flag=True, help="Run demo A")
@click.option("--b", "demo_b", is_flag=True, help="Run demo B")
@click.option("--c", "demo_c", is_flag=True, help="Run demo C")
@click.option("--timer", is_flag=True, help="Run timer context manager demo")
def cli(all, demo_a, demo_b, demo_c, timer):
    """Demonstration of click.timer and click.time_it features.

    This demo shows three ways to use @time_it decorator:

    \b
    写法 A：直接装饰命令函数
        @click.command()
        @click.time_it
        def cmd1(): pass

    \b
    写法 B：带参数装饰命令函数
        @click.command()
        @click.time_it(name="custom")
        def cmd2(): pass

    \b
    写法 C：装饰已有 Command 对象
        @click.time_it
        @click.command()
        def cmd3(): pass
    """
    if not any([all, demo_a, demo_b, demo_c, timer]):
        click.echo(cli.get_help(click.Context(cli)))
        return

    success = True

    if all or demo_a:
        if not demo_writing_a():
            success = False

    if all or demo_b:
        if not demo_writing_b():
            success = False

    if all or demo_c:
        if not demo_writing_c():
            success = False

    if all or timer:
        demo_timer_context_manager()

    click.echo("\n" + "=" * 50)
    if success:
        click.echo("所有演示执行成功！")
    else:
        click.echo("部分演示执行失败！")
    click.echo("=" * 50)


if __name__ == "__main__":
    cli()
