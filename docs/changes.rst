
import click

@click.command()
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name',
              help='The person to greet.')
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        click.echo(f"Hello {name}!")

if __name__ == '__main__':
    hello()
Và nó trông như thế nào khi chạy:

$ python hello.py --count=3
Your name: John
Hello John!
Hello John!
Hello John!
Nó tự động tạo các trang trợ giúp được định dạng độc đáo:

$ python hello.py --help
Usage: hello.py [OPTIONS]

  Simple program that greets NAME for a total of COUNT times.

Options:
  --count INTEGER  Number of greetings.
  --name TEXT      The person to greet.
  --help           Show this message and exit.
Bạn có thể lấy thư viện trực tiếp từ PyPI:

pip install click
Tài liệu 
Phần tài liệu này hướng dẫn bạn qua tất cả các kiểu sử dụng của thư viện.

Tại sao nhấp chuột?
Tại sao không Argparse?
Tại sao không phải là Docopt, v.v.?
Tại sao các hành vi được mã hóa cứng?
Tại sao không có Auto Correction?
Bắt đầu nhanh
virtualenv
Screencast và ví dụ
Các khái niệm cơ bản - Tạo lệnh
vang vọng
Lệnh làm tổ
Đăng ký lệnh sau
Thêm tham số
Chuyển sang Setuptools
Tích hợp công cụ thiết lập
Giới thiệu
Kiểm tra kịch bản
Tập lệnh trong Gói
Thông số
sự khác biệt
Parameter Types
Parameter Names
Implementing Custom Types
Options
Name Your Options
Basic Value Options
Multi Value Options
Tuples as Multi Value Options
Multiple Options
Counting
Boolean Flags
Feature Switches
Choice Options
Prompting
Password Prompts
Dynamic Defaults for Prompts
Callbacks and Eager Options
Yes Parameters
Values from Environment Variables
Multiple Values from Environment Values
Other Prefix Characters
Range Options
Callbacks for Validation
Optional Value
Arguments
Basic Arguments
Variadic Arguments
File Arguments
File Path Arguments
File Opening Safety
Environment Variables
Option-Like Arguments
Commands and Groups
Callback Invocation
Passing Parameters
Nested Handling and Contexts
Decorating Commands
Group Invocation Without Command
Custom Multi Commands
Merging Multi Commands
Multi Command Chaining
Multi Command Pipelines
Overriding Defaults
Context Defaults
Command Return Values
User Input Prompts
Option Prompts
Input Prompts
Confirmation Prompts
Documenting Scripts
Help Texts
Preventing Rewrapping
Truncating Help Texts
Meta Variables
Command Short Help
Help Parameter Customization
Complex Applications
Basic Concepts
Building a Git Clone
Advanced Patterns
Command Aliases
Parameter Modifications
Token Normalization
Invoking Other Commands
Callback Evaluation Order
Forwarding Unknown Options
Global Context Access
Detecting the Source of a Parameter
Managing Resources
Testing Click Applications
Basic Testing
File System Isolation
Input Streams
Utilities
Printing to Stdout
ANSI Colors
Pager Support
Screen Clearing
Getting Characters from Terminal
Waiting for Key Press
Launching Editors
Launching Applications
Printing Filenames
Standard Streams
Intelligent File Opening
Finding Application Folders
Showing Progress Bars
Shell Completion
Enabling Completion
Custom Type Completion
Overriding Value Completion
Adding Support for a Shell
Exception Handling
Where are Errors Handled?
What if I don’t want that?
Which Exceptions Exist?
Unicode Support
Surrogate Handling
Windows Console Notes
Unicode Arguments
Unicode Output and Input
API Reference
If you are looking for information on a specific function, class, or method, this part of the documentation is for you.

API
Decorators
Utilities
Commands
Parameters
Context
Types
Exceptions
Formatting
Parsing
Shell Completion
Testing
Miscellaneous Pages
click-contrib
Nâng cấp lên bản phát hành mới hơn
Nâng cấp lên 7.0
Nâng cấp lên 3.2
Nâng cấp lên 2.0
Giấy phép BSD-3-Khoản
thay đổi
Phiên bản 8.1.4
Phiên bản 8.1.3
Phiên bản 8.1.2
Phiên bản 8.1.1
Phiên bản 8.1.0
Phiên bản 8.0.4
Phiên bản 8.0.3
Phiên bản 8.0.2
Phiên bản 8.0.1
Phiên bản 8.0.0
Phiên bản 7.1.2
Phiên bản 7.1.1
Phiên bản 7.1
Phiên bản 7.0
Phiên bản 6.7
Phiên bản 6.6
Phiên bản 6.4
Phiên bản 6.3
Phiên bản 6.2
Phiên bản 6.1
Phiên bản 6.0
Phiên bản 5.1
Phiên bản 5.0
Phiên bản 4.1
Phiên bản 4.0
Phiên bản 3.3
Phiên bản 3.2
Phiên bản 3.1
Phiên bản 3.0
Phiên bản 2.6
Phiên bản 2.5
Phiên bản 2.4
Phiên bản 2.3
Phiên bản 2.2
Phiên bản 2.1
Phiên bản 2.0
Phiên bản 1.1
Phiên bản 1.0
Liên kết dự án
Quyên tặng
Bản phát hành PyPI
Mã nguồn
Người tìm bệnh
Trang mạng
Twitter
Trò chuyện
nội dung
Chào mừng đến với Click
Tài liệu
Tham chiếu API
Các trang khác
Tìm kiếm nhanh
Ẩn kết quả tìm kiếm

© Bản quyền 2014 Pallet. Được tạo bằng Sphinx 6.0.0.
  v: 8.1.x
