instagram_schema = {
    "name": "Instagram Profile",
    "baseSelector": "header section",  # Adjust based on Instagram's HTML structure
    "fields": [
        {
            "name": "username",
            "selector": "h2",
            "type": "text"
        },
        {
            "name": "full_name",
            "selector": "span:not([class])",
            "type": "text"
        },
        {
            "name": "bio",
            "selector": "div:not([class]) > span",
            "type": "text"
        },
        {
            "name": "post_count",
            "selector": "ul li:nth-child(1) span",
            "type": "text"
        },
        {
            "name": "followers",
            "selector": "ul li:nth-child(2) span",
            "type": "text"
        },
        {
            "name": "following",
            "selector": "ul li:nth-child(3) span",
            "type": "text"
        }
    ]
}