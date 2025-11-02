SCENARIOS = {
    "debate": {
        "description": "Two agents debate a topic, and one aims to persuade the other.",
        "agents": [
            {"name": "Alex", "role": "Pro side", "goal": "Argue in favor of the topic."},
            {"name": "Blake", "role": "Con side", "goal": "Argue against the topic."},
        ],
    },
    "startup_planning": {
        "description": "A startup team discusses features for an MVP product.",
        "agents": [
            {"name": "Ava", "role": "CEO", "goal": "Define the vision and priorities."},
            {"name": "Ben", "role": "Engineer", "goal": "Simplify scope and estimate effort."},
            {"name": "Mia", "role": "PM", "goal": "Align business goals and technical constraints."},
        ],
    },
    "story_writing": {
        "description": "Writers collaborate to create a short story idea.",
        "agents": [
            {"name": "Luna", "role": "Author", "goal": "Generate creative story ideas."},
            {"name": "Eli", "role": "Editor", "goal": "Improve clarity and coherence."},
        ],
    },
}
