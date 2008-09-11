model_renames = {
    "Option": ('Choice', 'BadName'),
}
field_renames = {
    "Poll": {
        "author": ('the_author',)
        "published_date": ('pub_date', 'publish_date')
    },
    "Option": {
        "votes": ('number_of_votes',)
    },
}