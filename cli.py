"""mini-auth 命令行工具"""
import asyncio

import typer

from app.core import sessions
from app.core.db import AsyncSessionLocal
from app.modules.user import curd as user_crud
from app.modules.user.schemas import UserCreate

app = typer.Typer(help="mini-auth 管理工具", no_args_is_help=True)


@app.callback()
def main() -> None:
    """mini-auth 管理工具"""


async def _create_user(
    username: str,
    password: str,
    email: str | None,
    is_admin: bool,
) -> None:
    async with AsyncSessionLocal() as session:
        if await user_crud.get_by_username(session, username):
            typer.secho(f"用户已存在: {username}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

        user = await user_crud.create(
            session,
            UserCreate(
                username=username,
                password=password,
                email=email,
                is_admin=is_admin,
            ),
        )

    typer.secho(
        f"已创建用户 id={user.id} username={user.username} admin={user.is_admin}",
        fg=typer.colors.GREEN,
    )


@app.command("create-user")
def create_user(
    username: str = typer.Argument(..., help="用户名"),
    password: str | None = typer.Option(
        None,
        "--password",
        "-p",
        help="密码 (省略则交互输入)",
    ),
    email: str | None = typer.Option(None, "--email", "-e", help="邮箱"),
    admin: bool = typer.Option(False, "--admin", "-a", help="设为管理员"),
) -> None:
    """创建用户"""
    if password is None:
        password = typer.prompt("密码", hide_input=True)
        confirm = typer.prompt("确认密码", hide_input=True)
        if password != confirm:
            typer.secho("两次密码不一致", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    asyncio.run(_create_user(username, password, email, admin))


async def _delete_user(username: str) -> None:
    async with AsyncSessionLocal() as session:
        user = await user_crud.get_by_username(session, username)
        if not user:
            typer.secho(f"用户不存在: {username}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

        if user.is_admin:
            others = await user_crud.count_active_admins(session, exclude_id=user.id)
            if others == 0:
                typer.secho(
                    "不能删除最后一个启用的管理员",
                    fg=typer.colors.RED,
                    err=True,
                )
                raise typer.Exit(code=1)

        user_id = user.id
        deleted_username = user.username
        await user_crud.delete(session, user)

    await sessions.delete_user_sessions(user_id)
    typer.secho(
        f"已删除用户 id={user_id} username={deleted_username}",
        fg=typer.colors.GREEN,
    )


@app.command("delete-user")
def delete_user(
    username: str = typer.Argument(..., help="用户名"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认"),
) -> None:
    """删除用户"""
    if not yes:
        typer.confirm(f"确定删除用户 {username}?", abort=True)
    asyncio.run(_delete_user(username))


if __name__ == "__main__":
    app()
