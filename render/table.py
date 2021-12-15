base = '\\ue0'
chars = '0123456789abcdef'

get_chars = lambda value : value.encode().decode( 'unicode_escape' )

def get_mapping() -> dict : return {
    
    escaped : get_chars( escaped )
    for second in chars
    for first in chars
    for escaped in ( base + second + first, )

}


def print_table() -> None : 

    mapping = get_mapping()

    for key, value in mapping.items() :

        print( key, value, sep = "\n" )


print_table()
