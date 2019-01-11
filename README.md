# xcstrings
Command-line tool to incrementally updating your Strings files from your Code and from Interface Builder files.

## Usage
``` bash
xcstrings.py -i <source_dir> [-i <source_dir>] -o <output_dir> [--ignore <keyword>] [--init] [--sort]
```

`-i` - path to source code directory

`-o` - path to directory with xx.lproj items

`--ignore` - keyword to skipping storyboard elements from localization. Default `#ignore`

`--init` - rewrite all localization files. **All existing translations will be lost**

`--sort` - reorder all strings by key


Add this script to **Build Phase** to update your Strings files on each build automatically.
Place `#ignore` string to your storyboard elements (`text` or `comment`) to skip them from syncing. 
