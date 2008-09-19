model_renames = {
    "Option": set(['case03_rename_model_badname', 'case03_rename_model_choice']),
}
field_renames = {
    "Poll": {
        "author": ('the_author',),
        "published_date": ('pub_date', 'publish_date'),
    },
    "Option": {
        "votes": ('number_of_votes',),
    },
}