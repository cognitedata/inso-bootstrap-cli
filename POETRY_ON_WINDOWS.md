## 220420 Windows + PowerShell + Python(s) + Poetry - lessons learned

- Added to Cognite internal "Python Develkoper Hub" documentation

### environment

- using a non-elevated PowerShell on Windows 10/11
- using elevation for Python installation (to make it available for "All Users")
  - not tested with out

### goal

- use `poetry` with support for different Python versions on Windows
- the solution requires
  - no `pyenv` and
  - only one (non python-version specific) path added to environment

### tl;dr summary of environment changes

```powershell
# local env changes or add to your ps profile or system environment
# set your default python
$env:PY_PYTHON='3.8'
# add installed poetry.exe to your path
$env:Path += ";$env:APPDATA\Python\Scripts"

# only required once
poetry config virtualenvs.in-project true
```

### steps

- installation of multiple Python version from [python.org](https://www.python.org/downloads/windows/) with this options:
  - _**Customize Installation**_
    1. "_Optional Features_" > as is
    2. "_Advanced Options_" >
       - "_Install for all Users_" (requires elevation)
       - "_Add Python to environment variables_"
       - [optional] I've installed all my versions in "_Customize install location_" folder (like `c:\peter-dev\Python\Python310`, a very old habit to avoid `C:\Program Files` path-issues having spaces)

    ```txt
    📂 C:\peter-dev\Python
    ┣ 📂 Python38
    ┣ 📂 Python39
    ┣ 📂 Python310
    ```

- checking which python version is active with the "Python Launcher for Windows"
  - python.org [documentation link](https://docs.python.org/3/using/windows.html#python-launcher-for-windows)

  ```powershell
  py --list
  Installed Pythons found by C:\WINDOWS\py.exe Launcher for Windows
  -3.10-64 *
  -3.9-64
  -3.8-64
  ```

  - FYI: installed in `C:\Windows\py.exe`, which don't require a `$env:Path` change

    ```powershell
    Get-Command py.exe

    CommandType     Name     Version    Source
    -----------     ----     -------    ------
    Application     py.exe   3.10.41... C:\WINDOWS\py.exe
    ```

- to switch from your "default python"

  ```powershell
  # name you version for this one command
  py -3.9

  # or
  py -3.10 -m pip install pandas
  ```

  ```powershell
  # for local testing, or persist in your system environment
  $env:PY_PYTHON='3.8'

  # check
  py --list
  Installed Pythons found by C:\WINDOWS\py.exe Launcher for Windows
  -3.10-64
  -3.9-64
  -3.8-64 *
  ```

- install poetry with official installer (with a tweak)
  - use `| py -` instead of `| python -`!

  ```ps
  # use `| py -` instead of `| python -`!
  (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

  # add to path (use double-quotes for $env variable expansion)
  $env:Path += ";$env:APPDATA\Python\Scripts"

  # check
  poetry --version

  Poetry version 1.1.13
  ```

- it is easier to manage poetry's `.venv` if they are inside the project-folder
  - instead all in `C:\Users\<youruser>\AppData\Local\pypoetry\Cache\virtualenvs`

  ```powershell
  # check virtualenvs.in-project
  poetry config --list
  virtualenvs.in-project = null

  # null means all venvs are created under 'virtualenvs.path'

  # change config
  poetry config virtualenvs.in-project true

  # check
  poetry config --list
  virtualenvs.in-project = true
  ```

- change directory into your poetry managed Python project
  - check your `pyproject.toml` for a

  ```toml
  [tool.poetry.dependencies]
  python = "^3.9"
  ```

  - in case it is not on the same Python version you are on
  - you need to point to the full path `python.exe` as `poetry` cannot find the versions on `$env:Path`

    ```powershell
    # not working on Windows with multiple Python installed
    # poetry env use 3.9
    # instead full path is required
    poetry env use C:\peter-dev\Python\Python39\python.exe

    Creating virtualenv inso-bootstrap-cli in C:\git\inso-bootstrap-cli\.venv
    Using virtualenv: C:\git\inso-bootstrap-cli\.venv
    ```

- now you should be able to finally run

  ```powershell
  poetry install

  # when finished successfully, run a quick test
  poetry run bootstrap-cli --help
  ```

### notes about running poetry preview version

- poetry update to `preview` breaks poetry
  - update to preview 1.2, causes poetry to break
  - reported [open issue#5377](https://github.com/python-poetry/poetry/issues/5377)

    ```powershell
    poetry self update --preview
    Updating Poetry to 1.2.0a2

    Poetry (1.2.0b1) is installed now. Great!

    PS C:\arwa\git\cog\inso-bootstrap-cli> poetry --version
    Traceback (most recent call last):
        File "C:\peter-dev\Python\Python38\lib\runpy.py", line 194, in _run_module_as_main
        return _run_code(code, main_globals, None,
        File "C:\peter-dev\Python\Python38\lib\runpy.py", line 87, in _run_code
        exec(code, run_globals)
        File "C:\Users\<username>\AppData\Roaming\Python\Scripts\poetry.exe\__main__.py", line 4, in <module>
    ImportError: cannot import name 'main' from 'poetry.console' (C:\Users\<username>\AppData\Roaming\pypoetry\venv\lib\site-packages\poetry\console\__init__.py)
    ```
  - installed in
    - `%AppData%\pypoetry\venv\Lib\site-packages\poetry`
  - temporary solution shared on [poetry gh-issue](https://github.com/python-poetry/poetry/issues/5377#issuecomment-1103879018)
      > Recognized that my `poetry.exe` from path `$env:APPDATA\Python\Scripts` has no updated timestamp after update. Copied over the one I found in `$env:APPDATA\pypoetry\poetry.exe`
      > => worked
