# Click 交互式命令行向导示例

本示例展示了 Click 新增的交互式命令行向导功能。

## 功能特性

### 1. 交互式命令 (InteractiveCommand)
- 自动提示用户输入所有参数
- 支持 `interactive_all` 模式，强制提示所有参数
- 支持 `interactive_skip` 跳过特定参数

### 2. 交互式命令组 (InteractiveGroup)
- 显示交互式菜单供用户选择子命令
- 当没有指定子命令时自动显示菜单

### 3. 交互式选项 (InteractiveOption)
- 支持条件提问 (`interactive_condition`)
- 支持顺序依赖 (`interactive_after`)
- 支持动态条件 (`interactive_when`)
- 支持交互式帮助 (`interactive_help`)

## 快速开始

### 1. 安装依赖

```bash
pip install flask flask-cors
```

### 2. 运行命令行示例

```bash
# 直接运行交互式命令
python interactive_demo.py

# 运行特定子命令
python interactive_demo.py echo-cmd
python interactive_demo.py copy
python interactive_demo.py process
```

### 3. 运行 Web API 服务器

```bash
python web_api.py
```

服务器将在 `http://localhost:5000` 启动。

### 4. 打开 Web 界面

在浏览器中打开 `index.html` 文件即可使用交互式 Web 界面。

## API 端点

### GET /api/commands
获取所有可用命令的信息。

### GET /api/commands/<command_path>
获取特定命令的详细信息。

### POST /api/execute
执行命令，支持交互式提示。

请求体:
```json
{
    "command": ["echo-cmd"],
    "args": [],
    "answers": ["Hello World", 3]
}
```

响应:
```json
{
    "status": "completed",
    "stdout": "1: Hello World\n2: Hello World\n3: Hello World\n",
    "stderr": "",
    "prompts": [...]
}
```

如果需要用户输入:
```json
{
    "status": "waiting_for_input",
    "prompt": {
        "type": "prompt",
        "text": "Message to echo?",
        "default": null
    },
    "prompts": [...]
}
```

## 使用示例

### 基础交互式命令

```python
import click
from click import interactive_command

@interactive_command()
@click.option('--name', prompt='What is your name?')
@click.option('--age', type=int, prompt='How old are you?')
def greet(name, age):
    click.echo(f'Hello {name}, you are {age} years old!')

if __name__ == '__main__':
    greet()
```

### 条件提问

```python
import click
from click import interactive_command, interactive_option

@interactive_command()
@click.option('--project-type', type=click.Choice(['python', 'javascript']))
@interactive_option(
    '--python-version',
    interactive_after='project_type',
    interactive_condition=lambda params: params.get('project_type') == 'python',
    prompt='Python version?',
    type=click.Choice(['3.8', '3.9', '3.10', '3.11', '3.12'])
)
@interactive_option(
    '--node-version',
    interactive_after='project_type',
    interactive_condition=lambda params: params.get('project_type') == 'javascript',
    prompt='Node.js version?',
    type=click.Choice(['16', '18', '20', '21'])
)
def create_project(project_type, python_version, node_version):
    click.echo(f'Creating {project_type} project...')
    if python_version:
        click.echo(f'Python version: {python_version}')
    if node_version:
        click.echo(f'Node.js version: {node_version}')
```

### 交互式命令组

```python
import click
from click import interactive_group

@interactive_group()
def cli():
    pass

@cli.command()
@click.option('--message', prompt='Message?')
def echo(message):
    click.echo(message)

@cli.command()
@click.option('--source', prompt='Source?')
@click.option('--dest', prompt='Destination?')
def copy(source, dest):
    click.echo(f'Copying {source} to {dest}')

if __name__ == '__main__':
    cli()
```

## 新增的装饰器和类

### 装饰器
- `@interactive_command` - 创建交互式命令
- `@interactive_group` - 创建交互式命令组
- `@interactive_option` - 创建交互式选项
- `@with_interactive` - 添加 `--interactive` 标志

### 类
- `InteractiveCommand` - 交互式命令类
- `InteractiveGroup` - 交互式命令组类
- `InteractiveOption` - 交互式选项类

## 参数说明

### InteractiveOption 参数
- `interactive` - 是否启用交互式模式
- `interactive_when` - 动态条件函数，接收 Context
- `interactive_after` - 依赖的参数名称
- `interactive_condition` - 条件函数，接收已处理的参数字典
- `interactive_help` - 交互式帮助文本

### InteractiveCommand 参数
- `interactive` - 是否启用交互式模式
- `interactive_all` - 是否提示所有参数
- `interactive_skip` - 跳过的参数名称列表

### InteractiveGroup 参数
- `interactive` - 是否启用交互式模式
- `interactive_menu` - 是否显示交互式菜单

## 测试

### 命令行测试

```bash
# 测试简单问候
python interactive_demo.py simple-greet

# 测试条件提问
python interactive_demo.py create-project

# 测试交互式菜单
python interactive_demo.py
```

### Web 界面测试

1. 启动 API 服务器: `python web_api.py`
2. 打开 `index.html`
3. 选择命令并点击执行
4. 按照提示输入答案

## 注意事项

1. 确保 Python 版本 >= 3.8
2. Web API 需要 Flask 和 Flask-CORS
3. 交互式功能与现有的 Click 参数解析系统完全兼容
4. 条件提问支持复杂的业务逻辑
