# Piperift's CICD Scripts

## Unreal Engine plugins
### Packaging manually

Building the source code:
```bash
py build.py plugin -n {plugin_name} -p {plugin_files_path}
```

Run the tests in asolation:
```bash
py test.py plugin -n {plugin_name} -p {plugin_files_path}
```

Compress build:
```bash
py compress.py plugin -n {plugin_name} -p {plugin_files_path}
```

Resulting packaged build can be found at {plugin_files_path}/Package
