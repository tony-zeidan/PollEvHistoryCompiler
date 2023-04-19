# PollEvHistoryCompiler
Have you ever wanted to compile your Poll Everywhere history into a more usable form?
This project allows you to use a script to load it into almost any form you want!
You can filter by presenter, and use different types of encodings so that you can load polls with almost any data in them.
Right now most of the support is for `Multiple choice` type polls.

## Installation
There are two approaches to the installation of this package/script.
Clone the repository, and within the root folder run:

```
pip install .
```

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
pollev-compiler <INPUT CSV> <TRANSFORM (json, yaml, toml, etc.)>  --output-file <OUTPUT PATH (dir)> --remove_hidden
```

Remove image-related questions from the result:
```
pollev-compiler <INPUT CSV> <TRANSFORM (json, yaml, toml, etc.)>  --output-file <OUTPUT PATH (dir)> --remove_images
```

Markdown format is now supported! 
```
pollev-compiler <INPUT CSV> markdown
```
This process uses `markdownify` to turn the pre-existing HTML functionality into a markdown file.

You can now use the `--quiz_mode` option in the `html` transform to turn the output to a interactable quiz that highlights your guesses,
and your score on the quiz (correct over total). You can do this like:
```
pollev-compiler <INPUT CSV> html --quiz_mode
```
The output consists of a JavaScript file, CSS file, and HTML file. Without quiz mode, the JavaScript file isn't added.


## Documentation
