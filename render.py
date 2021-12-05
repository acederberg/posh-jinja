from jinja2 import Environment, FileSystemLoader, select_autoescape
from os.path import join
import json
import yaml
import re

TEMPLATES = './templates'
PALETTES = './palettes'
BUILD = './build'
YAML = re.compile( '.(?i)yaml' )
JINJA = re.compile( '.(?i)j2' )
JSON = re.compile( '.(?i)json' )
HEX = re.compile( '^#([A-Fa-f0-7]{3}|[A-Fa-f0-7]{6})$' )



class UndefinedLoader( Exception ): pass


class InadmissibleValue( Exception ): pass


def is_json( path ) -> bool: return bool( JSON.search( path ) )


def is_yaml( path ) -> bool: return bool( YAML.search( path ) )


def get_attr( path, attr ): 
    " The the appropriate loader for a color palette "
    if is_json( path ): return getattr( json, attr )
    elif is_yaml( path ): return getattr( yaml, attr )
    else : raise UndefinedLoader()

def get_load( path ): return get_attr( path, 'load' )
def get_dump( path ): return get_attr( path, 'dump' )

def load_palette( palette_name ) -> dict:
    "load a color scheme from a json or yaml"
    with open( join( PALETTES, palette_name ) ) as file : return get_load( palette_name )( file )


def render_pallete_validation_message( bad_items : dict ) -> str: 
    return "Bad values: " + ", ".join( f"{key} = {value}" for key, value in bad_items.items() )


def validate_palette( palette : dict ) -> bool:
    "Validate a palette. If it fails, raise an error describing exactly what is wrong with it."
    try : 
        print( palette )
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
    validate_palette( palette ) 

    return palette


Env = Environment(
    loader =  FileSystemLoader( TEMPLATES )
)


def render_template( template_name : str, palette_name : str ) -> str:

    palette = get_palette( palette_name )
    template = Env.get_template( template_name )
    rendered = template.render( **palette )
    return rendered


def build_template( template_name : str, palette_name : str ) -> None:
    
    extension = '.json' if is_json( template_name ) else (
        '.yaml' 
        if is_yaml( template_name ) 
        else None
    )
    if extension is None : raise Exception( "Template must have a json or yaml extension" )

    template_destination = join( 
        BUILD,
        re.sub( JINJA, '', template_name )
    )

    template_rendered = render_template( template_name, palette_name )
    with open( template_destination, 'w' ) as file: file.writelines( template_rendered )


def main():
    from sys import argv

    if not len( argv ) == 3: raise Exception( "Requires exactly two arguements." )

    _, template_name, palette_name = argv

    build_template( template_name, palette_name )


if __name__ == "__main__" :

    main()
