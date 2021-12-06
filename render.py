from jinja2 import Environment, FileSystemLoader, select_autoescape
from os.path import join, abspath
import json
import yaml
import re

json_, yaml_ = "json", "yaml"
EXTENSIONS = { json_ : json, yaml_ : yaml }
TEMPLATES = './templates'
PALETTES = './palettes'
BUILD = './build'
YAML = re.compile( '.(?i)yaml' )
JINJA = re.compile( '.(?i)j2' )
JSON = re.compile( '.(?i)json' )
HEX = re.compile( '^#([A-Fa-f0-7]{3}|[A-Fa-f0-7]{6})$' )

# Path tools

def rendered_path( template_name ):
    return abspath( join( 
        BUILD,
        re.sub( JINJA, '', template_name )
    ) )


def template_path( template_name ):
    return abspath( join(
        TEMPLATES,
        template_name
    ) )


# ERRORS, regex, utilities.


class UndefinedLoader( Exception ): pass


class InadmissibleValue( Exception ): pass


def is_json( path ) -> bool: return bool( JSON.search( path ) )


def is_yaml( path ) -> bool: return bool( YAML.search( path ) )


def json_else_yaml( if_is_json, if_is_yaml ):
    def wrapper( path ):
        print( f"{ path = }, { is_json( path ) = }, { is_yaml( path ) = } " )
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


get_load = json_else_yaml(
    lambda path : json.load,
    lambda path : (
        lambda filestream : yaml.load( 
            filestream, 
            Loader = yaml.FullLoader 
        )
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


# PALETTE METHODS.

def load_palette( palette_name ) -> dict:
    "load a color scheme from a json or yaml"

    with open( join( PALETTES, palette_name ) ) as file : 
        load = get_load( palette_name )
        print( get_extension( palette_name ) ) 
        print( load ) 
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


# JINJA
Env = Environment(
    loader =  FileSystemLoader( TEMPLATES )
)


def render_template( template_name : str, palette_name : str ) -> str:

    palette = get_palette( palette_name )
    template = Env.get_template( template_name )
    rendered = template.render( **palette ) if palette else None
    return rendered


def build_template( template_name : str, palette_name : str ) -> None:
    
    extension = '.json' if is_json( template_name ) else (
        '.yaml' 
        if is_yaml( template_name ) 
        else None
    )
    if extension is None : raise Exception( "Template must have a json or yaml extension" )

    template_destination = rendered_path( template_name )

    template_rendered = render_template( template_name, palette_name )
    if not template_rendered: raise Exception( "Template not rendered" )
    with open( template_destination, 'w' ) as file: file.writelines( template_rendered )


# COMMANDLINE
def main():
    from sys import argv

    if not len( argv ) == 3: raise Exception( "Requires exactly two arguements." )

    _, template_name, palette_name = argv

    build_template( template_name, palette_name )


if __name__ == "__main__" :

    main()
