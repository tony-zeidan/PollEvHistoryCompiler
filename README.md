# PollEvHistoryCompiler
A compiler of Poll Everywhere history results.

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
