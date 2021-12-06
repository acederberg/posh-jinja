from render import fix_escape

print( fix_escape({ "food" : "\\ufd66", "bar" : "aerhg" }) )

print( fix_escape({
    "food" : "\\ufd33",
    "bar" : [
        'spam',
        {
            'eggs' : "\\ufd33"
        },
        "\\ufd33"
    ]
}))
