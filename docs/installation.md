# Installation Guide

This guide will walk you through setting up a Python virtual environment with the necessary
dependencies installed.

## Environment Setup

Setting up your environment is done in three steps: installing native dependencies, cloning the
pntOS-Python Exercises project, and setting up your Python environment.

### Install Native Dependencies

Please ensure you have the following packages installed and available on your system:

| Package              | Reason Needed                      |
| -------------------- | ---------------------------------- |
| Python 3.10 or later | Needed to run Apps                 |
| Git                  | Needed to acquire dependencies     |
| Glib2                | Needed for LCM tools, to run Apps  |
| Tkinter              | Needed for plotting filter results |

Ubuntu 22.04 users can use the following command to install the above packages:

```shell
sudo apt update && sudo apt install python3 python3-venv git libglib2.0-dev python3-tk
```

Users of other operating systems will need to install the above packages using
their operating system's package manager.

### Cloning pntOS-Python Exercises

Next, download the pntOS-Python Exercises project onto your machine. While there are several
approaches to do so, we suggest you clone the [`pntOS-Python Exercises Git
repository`](https://github.com/is4s/pntOS-Python-Exercises) using:

```shell
git clone https://github.com/is4s/pntOS-Python-Exercises.git
```

Then switch your current working directory to the directory you just created with:

```shell
cd pntOS-Python-Exercises
```

Finally, you are now ready to set up your Python environment in the next section.

### Python Environment Setup

This project supports two workflows:

- **pip:** the traditional Python package manager.
- **uv:** a modern, faster, all-in-one alternative to pip.

If you are new to Python development, it is recommended that you use the pip workflow.
Choose your preferred approach below:

```````{tab-set}
``````{tab-item} **pip**

We will begin by creating and entering a clean Python virtual environment (venv). We can create the
virtual environment in the `.venv` folder by running the following command in the project root
directory:

```shell
python3 -m venv .venv --prompt pntos-python-exercises
```

Next, enter the virtual environment. The steps to do this vary depending on your shell:

```{include} activate_venv.md
```

<br>
Your shell should now be inside the virtual environment. It is recommended that you upgrade your pip
to the latest:

```shell
pip install --upgrade pip
```

Now we're ready to install the dependencies. In the project root directory, run:

```shell
pip install -v -r requirements.txt
```

```{note}
This command may take a while to run. It is downloading example data, which may take a lot
of bandwidth.
```

``````
``````{tab-item} **uv**

First, ensure you have uv installed. If you don't have it yet, you can install it by
following the instructions at
[https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/).

Create a virtual environment using uv in the project root directory and import
python dependencies in one step:

```shell
uv sync
```

```{note}
This command may take a while to run. It is downloading example data, which may take a lot
of bandwidth.
```

Next, enter the virtual environment:

```{include} activate_venv.md
```

``````
```````

## Next Steps

Assuming the above was successful, you are ready to continue. If you came here from [the main menu's
set up instructions](#set-up-target), you can return now.
