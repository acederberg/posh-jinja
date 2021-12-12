# posh-jinja

Just something I made messing around.
Use jinja templates to make posh configs ( and similar documents ) using different color pallets in either YAML or JSON format. Includes

1. A `python` file, render.py inside of the `render` folder.
2. A template ( the `.omp` extension is for `oh-my-posh` ).
3. Some palettes.
4. `build.yaml`


## Use

Using a single keyword will try to read a file like `build.yaml` and make the specified themes, e.g.

~~~bash
python3 ./render/render.py build.yaml
~~~

will create the templates described in `build.yaml`.


## About `build.yaml`

This should be something like the following

~~~yaml
# build.yaml

render :

- template_name : <Required. Some file in the `TEMPLATES` directory.>
  palette_name : <Required. Some file in the `PALETTES` directory.>
  target_format : <Optional. Defaults to the template format.>
  target_name : <Optional. Defaults to the template name.>

...
~~~

but may also be written as a `JSON` document.


# Preserving Go Templates

Since `oh-my-posh` use Go templates which are very similar to `jinja2` templates, the `raw` block must be used. For instance, the templates

~~~yaml
# Bad templating

background_templates :
- "{{ if or (.Working.Changed) (.Staging.Changed) }}{{ brightRed }}{{ end }}"
- "{{ if and (gt .Ahead 0) (gt .Behind 0) }}{{ brightPurple }}{{ end }}"
- "{{ if gt .Ahead 0 }}{{ yellow }}{{ end }}"
- "{{ if gt .Behind 0 }}{{ brightGreen }}{{ end }}"

~~~

should be written

~~~.yaml.j2
# Good templating

background_templates :
- "{% raw %}{{ if or (.Working.Changed) (.Staging.Changed) }}{% endraw %}{{ brightRed }}{% raw %}{{ end }}{% endraw %}"
- "{% raw %}{{ if and (gt .Ahead 0) (gt .Behind 0) }}{% endraw %}{{ brightPurple }}{% raw %}{{ end }}{% endraw %}"
- "{% raw %}{{ if gt .Ahead 0 }}{% endraw %}{{ yellow }}{% raw %}{{ end }}{% endraw %}"
- "{% raw %}{{ if gt .Behind 0 }}{% endraw %}{{ brightGreen }}{% raw %}{{ end }}{% endraw %}"

~~~

when template values are to be included. Alternatively when no template values are necessary:

~~~.yaml.j2
# Good templating

background_templates :
{% raw %}
- "{{ if or (.Working.Changed) (.Staging.Changed) }}{{ brightRed }}{{ end }}"
- "{{ if and (gt .Ahead 0) (gt .Behind 0) }}{{ brightPurple }}{{ end }}"
- "{{ if gt .Ahead 0 }}{{ yellow }}{{ end }}"
- "{{ if gt .Behind 0 }}{{ brightGreen }}{{ end }}"
{% endraw %}
~~~

