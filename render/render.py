from jinja2 import Environment, FileSystemLoader, select_autoescape
from os.path import join, abspath, basename
import json
import yaml
import re

json_, yaml_, jinja_ = "json", "yaml", "jinja_"
EXTENSIONS = { json_ : json, yaml_ : yaml }
TEMPLATES = abspath( './templates' )
PALETTES = abspath( './palettes' )
BUILD = abspath( './build' )
YAML = re.compile( '.(?i)yaml' )
JINJA = re.compile( '.(?i)j2' )
JSON = re.compile( '.(?i)json' )
HEX = re.compile( '^#([A-Fa-f0-7]{3}|[A-Fa-f0-7]{6})$' )
FORMATS = {
    yaml_ : YAML,
    json_ : JSON,
    jinja_ : JINJA 
}
STRINGS = {
    value : '.' + key
    for key,value in FORMATS.items()
}
INVERSE = {
    YAML : JSON,
    JSON : YAML
}


# Path tools

def rendered_path_from_template_name( template_name : str, target_format ) -> str :
        
    # Remove the jinja extension.
    no_jinja = re.sub( JINJA, '', template_name )
    print( f"{ no_jinja = }" )
    # If the name is not in the target format, substitute the current format with the opposite.
    if target_format and not target_format.search( template_name ): no_jinja = re.sub( 
        INVERSE[ target_format ], 
        STRINGS[ target_format ], 
        no_jinja 
    )
    print( f"{ no_jinja = }" )

    return join( 
        BUILD,
        no_jinja 
    )


def rendered_path_from_target_name( target_name : str, target_format ) -> str :

    # When both a name and format are provided and the format is not specified in the name, add the format.
    if not no_target_format and not target_name.search( target_format ): 
        target_name += '.omp' + '.'.join( 
            key 
            for key, value in FORMATS.items()
            if value == target_format
        )
    return join(
        BUILD,
        target_name
    )


def rendered_path( target_name : str = None, template_name : str = None, target_format = None) -> str :
    """
    Take a template name and a target format ( regex ) and make the absolute path to the result.
    If the 'name' field is provided, makes a name with the target format if no format is matched within name.
    """
    print( f"{ target_name = }, { template_name = }, { target_format = }" )
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

    if all_but_name or all( not item for item in everything ): return rendered_path_from_template_name( template_name, target_format )
    elif not no_name : return rendered_path_from_target_name( target_name, target_formate )
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


def switch( path ):
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
        print( template )
        dump( template, writefile, )


def build_template( template_name : str, palette_name : str, target_format : str = None ) -> None:
    
    extension = get_extension( template_name )
    extension_is_target_format = extension == target_format
    target_format = FORMATS[ target_format ] if target_format else None

    if extension is None : raise Exception( "Template must have a json or yaml extension" )

    destination = rendered_path( 
        template_name = template_name, 
        target_format = target_format if extension_is_target_format else None
    )

    print( f"{ destination = }" )
    template_rendered = render_template( template_name, palette_name )

    if not template_rendered: raise Exception( "Template not rendered" )
    with open( destination, 'w' ) as file: file.writelines( template_rendered )

    if not extension_is_target_format : switch( destination )


# COMMANDLINE
def main():
    from sys import argv

    n = len( argv )
    if not ( 4 >= n >= 3 ): raise Exception( "Requires between 2 and 4 arguements." )

    build_template(  *argv[1:4] )


if __name__ == "__main__" :

    main()
