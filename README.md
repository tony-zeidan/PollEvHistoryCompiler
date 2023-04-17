# PollEvHistoryCompiler
Have you ever wanted to compile your Poll Everywhere history into a more usable form?
This project allows you to use a script to load it into almost any form you want!
You can filter by presenter, and use different types of encodings so that you can load polls with almost any data in them.
Right now most of the support is for `Multiple choice` type polls.

## Installation
There are two approaches to the installation of this package/script.
1) 

Clone the repository, and within the root folder run:

```
pip install .
```

2)

Install the package from PyPI:

```
pip install pollev-history-compiler
```

## Usage
It works as follows as a command-line script.
```
pollev-compiler <INPUT CSV> <TRANSFORM (json, yaml, toml, etc.)> --output-file <OUTPUT PATH (dir)> <OPTIONS>
```

If no output path is supplied, the script will use the 

Good options include presenter name:
```
pollev-compiler <INPUT CSV> <TRANSFORM (json, yaml, toml, etc.)>  --output-file <OUTPUT PATH (dir)> --presenter <NAME> <OPTIONS>
```

Remove hidden questions from the result:
```
pollev-compiler <INPUT CSV> <TRANSFORM (json, yaml, toml, etc.)>  --output-file <OUTPUT PATH (dir)> --rhidden
```

## Documentation
