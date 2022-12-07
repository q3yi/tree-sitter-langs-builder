# Build tree-sitter language definition for emacs 29

A python script to help build tree-sitter language definition for
emacs 29 core treesit intergration.

required python: >= 3.10.8

build language definition provided by tree-sitter organization:

```shell
./treesitter.py bash c
```

build language definition provided by thrid party:

```shell
./treesitter.py --github-org WhatsApp erlang
```

build with any remote git repository:

```shell
./treesitter.py --repo 'https://github.com/tree-sitter/tree-sitter-bash.git' bash
```

batch build with json config:

```json
[
  {
	"language": "bash",
	"repo": "https://github.com/tree-sitter/tree-sitter-bash.git"
  },
  {
	"language": "c",
	"repo": "https://github.com/tree-sitter/tree-sitter-c.git"
  }
]
```

```shell
./treesitter.py --batch-json batch.json
```

All build command and necessary header files are copied from the repo
[tree-sitter-module](https://github.com/casouri/tree-sitter-module),
which created by @casouri.
