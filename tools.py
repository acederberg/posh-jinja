import json
import yaml
from render import BUILD, JINJA, JSON, YAML, is_yaml, is_json, yaml_, json_, json_else_yaml, get_load, get_dump, rendered_path, template_path 
from os.path import join, basename, abspath
import re

get_compliment = json_else_yaml(
    lambda path : '.' + yaml_,
    lambda path : '.' + json_
)


_compliment_rendered_path = lambda EXTN, extn_, path : abspath(
    join( 
        BUILD,
        re.sub( 
            EXTN, 
            '.' + extn_, 
            basename( path ) 
        )
    )
)

compliment_rendered_path = json_else_yaml(
    lambda path : _compliment_rendered_path( JSON, yaml_, path ),
    lambda path : _compliment_rendered_path( YAML, json_, path )
)


def switch( template_name ):
    " Take template or rendered template and switch it to the complementing format. "
    compliment = get_compliment( template_name ) 
    if compliment is None: raise Exception( "Invalid file type" )
    load = get_load( template_name )
    dump = get_dump( '.' + compliment )

    with open( 
        template_path( template_name ),
        "r"
    ) as readfile, open( 
        compliment_rendered_path( template_name ),
        "w"
    ) as writefile:
        template : dict = load( readfile )
        print( template, writefile )
        dump( template, writefile, )

    print( f"{load = }, { dump = }" )

switch( "my_theme.omp.yaml.j2" )

