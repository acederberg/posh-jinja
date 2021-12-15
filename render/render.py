from jinja2 import Environment, FileSystemLoader, select_autoescape
from shutil import rmtree
from os import mkdir
from os.path import join, abspath, basename, dirname, exists
import json
import yaml
import re

from typing import Callable

# TYPE DEFINITIONS

regex = type( re.compile("") )


# VARIABLES
json_, yaml_, jinja_ = "json", "yaml", "jinja_"

DIRNAME : str = abspath( join( dirname( __file__ ), '..' ) )
get_location = lambda foldername : join( DIRNAME, foldername )

TEMPLATES : str = get_location( 'templates' )
PALETTES : str = get_location( 'palettes' )
BUILD : str = get_location( 'build' )

YAML : regex = re.compile( '.(?i)yaml' )
JINJA : regex = re.compile( '.(?i)j2' )
JSON : regex = re.compile( '.(?i)json' )
HEX : regex = re.compile( '^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$' )


# DERIVED VARIABLES
 
EXTENSIONS : dict = { json_ : json, yaml_ : yaml }

FORMATS : dict = {
    yaml_ : YAML,
    json_ : JSON,
    jinja_ : JINJA 
}


STRINGS : dict = {
    value : '.' + key
    for key,value in FORMATS.items()
}


INVERSE : dict = {
    YAML : JSON,
    JSON : YAML
}


# JINJA

ENV = Environment( loader =  FileSystemLoader( TEMPLATES ) )


# PATHS

def rendered_path_from_template_name( template_name : str, target_format : regex ) -> str :
    """ Make the pathname to save a rendered template to based off of its name and the target format.  """

    # Remove the jinja extension.
    no_jinja = re.sub( JINJA, '', template_name )

    # If the name is not in the target format, substitute the current format with the opposite.
    if target_format and not target_format.search( template_name ): no_jinja = re.sub( 
        INVERSE[ target_format ], 
        STRINGS[ target_format ], 
        no_jinja 
    )

    return join( 
        BUILD,
        no_jinja 
    )


def rendered_path_from_target_name( target_name : str, target_format : regex ) -> str :
    """ Make path name from a name and a `target_format`. """
    
    # When both a name and format are provided and the format is not specified in the name, add the format.
    if target_format and not target_format.search( target_name ): 
        
        target_name += '.omp.' + '.'.join( 
            key 
            for key, value in FORMATS.items()
            if value == target_format
        )

    return join(
        BUILD,
        target_name
    )


def rendered_path( target_name : str = None, template_name : str = None, target_format : regex = None) -> str :
    """
    Take a template name and a target format ( regex ) and make the absolute path to the result.
    If the 'name' field is provided, makes a name with the target format if no format is matched within name.
    """
    
    everything = (
        item is None
        for item in (
            template_name, 
            target_format, 
            target_name
        )
    )  
    
    no_template_name, no_target_name, no_target_format = everything
    all_but_name = no_template_name and ( not no_target_name ) and ( not no_target_format )

    if not target_format : target_format = YAML if YAML.search( template_name ) else JSON

    if not no_target_name or all( not item for item in everything ): return rendered_path_from_target_name( target_name, target_format )
    elif all_but_name : return rendered_path_from_template_name( template_name, target_format )
    else : raise Exception( "Insufficient arguements to `rendered_path`" )
        
        
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


def template_path( template_name : str ):
    return abspath( join(
        TEMPLATES,
        template_name
    ) )


# ERRORS, regex, utilities.


class UndefinedLoader( Exception ): pass


class InadmissibleValue( Exception ): pass


def is_json( path : str ) -> bool: return bool( JSON.search( path ) )


def is_yaml( path : str ) -> bool: return bool( YAML.search( path ) )


def json_else_yaml( if_is_json : Callable , if_is_yaml : Callable ):
    def wrapper( path ):
        return if_is_json( path ) if is_json( path ) else (
            if_is_yaml( path ) 
            if is_yaml( path )
            else None
        )
    return wrapper
   

get_extension = json_else_yaml(
    lambda path : json_,
    lambda path : yaml_
)


get_compliment = json_else_yaml(
    lambda path : '.' + yaml_,
    lambda path : '.' + json_
)


get_load = json_else_yaml(
    lambda path : json.load,
    lambda path : (
        lambda filestream : fix_escape( yaml.load( 
            filestream, 
            Loader = yaml.FullLoader 
        ) )
    )
)

get_dump = json_else_yaml(
    lambda path : (
        lambda data, filestream : json.dump( 
            data, 
            filestream, 
            indent = 4 
        )
    ),
    lambda path : yaml.dump
)


compliment_rendered_path = json_else_yaml(
    lambda path : _compliment_rendered_path( JSON, yaml_, path ),
    lambda path : _compliment_rendered_path( YAML, json_, path )
)


# Method to fix messed up escape characters
fix_value = lambda value : value.encode().decode( 'unicode_escape' ) if '\\' in value else value
fixable = lambda value : ( type( value ) == list ) or ( type( value ) == dict )

def fix_escape( data ): return {
    key : fix_value( value )
    if type( value ) == str
    else (
        fix_escape( value )
        if fixable( value )
        else value
    )
    for key, value in data.items()
} if type( data ) == dict else (
    [
        fix_value( value )
        if type( value ) == str
        else (
            fix_escape( value )
            if fixable( value )
            else value
        )
        for value in data
    ] 
    if type( data ) == list
    else
        data
)
    

# PALETTE METHODS.

def load_palette( palette_name : str ) -> dict:
    "load a color scheme from a json or yaml"

    with open( join( PALETTES, palette_name ) ) as file : 
        load = get_load( palette_name )
        return load( file ) if load else None


def render_pallete_validation_message( bad_items : dict ) -> str: 
    
    return "Bad values: " + ", ".join( f"{key} = {value}" for key, value in bad_items.items() )


def validate_palette( palette : dict ) -> bool:
    
    "Validate a palette. If it fails, raise an error describing exactly what is wrong with it."

    try : 
        bad = {
            key : value
            for key, value in palette.items() 
            if not HEX.search( value ) 
        }
        if not bad: return True
        else : raise InadmissibleValue( render_pallete_validation_message( bad ) )

    except Exception as err: raise InadmissibleValue( err )


def get_palette( palette : dict ) -> dict:
    "Load and validate a palette"
    
    palette = load_palette( palette ) 
    if not palette : return None
    validate_palette( palette ) 

    return palette


def switch( path : str ) -> None :

    " Take template or rendered template and switch it to the complementing format. "

    compliment = get_compliment( path )
    if compliment is None: raise Exception( "Invalid file type" )

    load = get_load( path )
    dump = get_dump( '.' + compliment )

    with open(
        path,
        "r"
    ) as readfile, open(
        compliment_rendered_path( path ),
        "w"
    ) as writefile:
        template : dict = load( readfile )
        dump( template, writefile, )


def _render_from_template( template_name : str, palette_name : str ) -> str:
    """ Helper function for _render_from_template. """

    palette = get_palette( palette_name )
    template = ENV.get_template( template_name )
    rendered = template.render( **palette ) if palette else None
    return rendered


def render_from_template( template_name : str, palette_name : str, target_format : str = None, target_name : str = None ) -> None:
   
    """
    Render from a template and a palette. 
    For concistant rebuilds, try using a configuration file. See `render_from_config`.
    """

    extension = get_extension( template_name )
    extension_is_target_format = extension == target_format
    target_format = FORMATS[ target_format ] if target_format else None
    
    if extension is None : raise Exception( "Template must have a json or yaml extension" )

    destination = rendered_path( 
        template_name = template_name, 
        target_name = target_name,
        target_format = target_format if extension_is_target_format else None
    )

    template_rendered = _render_from_template( template_name, palette_name )

    if not template_rendered: raise Exception( "Template not rendered" )
    with open( destination, 'w' ) as file: file.writelines( template_rendered )

    if not extension_is_target_format : switch( destination )




def render_from_config( config_path : str ) -> None :
    """
    Render templates using a configuration file. The configuration file is either a yaml or a json like such:
    ~~~yaml
    render :
        - template_name : <Required. Some file in the `TEMPLATES` directory.>
          palette_name : <Required. Some file in the `PALETTES` directory.>
          target_format : <Optional. Defaults to the template format.>
          target_name : <Optional. Defaults to the template name.>

        ...
    ~~~
    """

    fields = ( 'target_name', 'target_format', 'template_name', 'palette_name' )
    
    with open( config_path, 'r' ) as file : 
        
        load = get_load( config_path )
        config = load( file )

    if 'render' in config: config = config[ 'render' ]

    exists( BUILD ) and rmtree( BUILD )
    mkdir( BUILD )
    for item in config :
    
        args = { 
            key : item[ key ]
            for key in fields
            if key in item
        } 
        render_from_template( **args )


# COMMANDLINE
def main() -> None :
    
    """
    Only one arguement will result in calling `render_from_config`.
    Two to three arguements will result in calling render.
    
    *NB: argv will have this files name as the zeroth arguement.*
    """

    from sys import argv

    args = argv[ 1 : ]
    n = len( args )
    if n == 1 : render_from_config( *args )
    elif 3 >= n >= 2 : render_from_template( *args )
    else : raise Exception( "Insufficient arguements." )

    
if __name__ == "__main__" :

    main()
