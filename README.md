# PollEvHistoryCompiler
Have you ever wanted to compile your Poll Everywhere history into a more usable form?
This project allows you to use a script to load it into almost any form you want!
You can filter by presenter, and use different types of encodings so that you can load polls with almost any data in them.
Right now most of the support is for `Multiple choice` type polls.

## Usage
It works as follows as a command-line script.
```
python reader.py <INPUT CSV> <TRANSFORM (json, yaml, toml, etc.)> --output-file <OUTPUT PATH (dir)> <OPTIONS>
```

Good options include presenter name:
```
python reader.py <INPUT CSV> <TRANSFORM (json, yaml, toml, etc.)>  --output-file <OUTPUT PATH (dir)> --presenter <NAME> <OPTIONS>
```

Remove hidden questions from the result:
```
python reader.py <INPUT CSV> <TRANSFORM (json, yaml, toml, etc.)>  --output-file <OUTPUT PATH (dir)> --rhidden
```

## Documentation
