To generate a graph visualization from a `*.gv` file in this directory, there
are a couple things you can do:
* On Fedora 28+
  * Install `python-xdot` from `dnf`
  * view file with `xdot /path/to/graph_you_want_to_see.gv`
* On MacOS:
  * Get [graphviz](https://graphviz.gitlab.io/download/)
  * Use the [dot program](https://graphviz.gitlab.io/_pages/pdf/dotguide.pdf) to render a graph. Use the `-T` flag to specify the desired output format. For example, `dot -Tjpg graph.gv -o graph.jpg`
