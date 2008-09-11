model_renames = {
}
field_renames = {
    "Poll": {
        "author": ('the_author',)
        "published_date": ('pub_date', 'publish_date')
    },
    "Choice": {
        "number_of_votes": ('votes',)
    },
}