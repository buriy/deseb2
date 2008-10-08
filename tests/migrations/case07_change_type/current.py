model_renames = {
}
field_renames = {
    "Poll": {
        "author": ('the_author',),
        "pub_date": ('pub_date', 'publish_date'),
        "the_author": ('the_author',),
        "published_date": ('pub_date', 'publish_date'),
    },
    "Choice": {
        "votes": ('votes',),
        "number_of_votes": ('votes', 'num_votes'),
        "option": ('choice',),
    },
}