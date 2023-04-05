"""Основной модуль приложения."""
import click


@click.group()
@click.pass_context
def cli(ctx: click.core.Context):
    """Инициализирует настройки для процессов приложения"""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings
    click.echo("Configuration loaded")


@cli.command(help="Explanation.")
@click.pass_context
def run_worker_results_receiver(ctx: click.core.Context):
    """
    """
    ctx_settings: CommonSettings = ctx.obj["settings"]


if __name__ == "__main__":
    cli(  # pylint: disable = no-value-for-parameter, unexpected-keyword-arg
        obj={}
    )
