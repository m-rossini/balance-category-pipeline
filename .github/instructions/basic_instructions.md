---
applyTo: '**'
---

* Before work:
    * Make sure you are aware of previous decisions and design that are located under summaries
    * Understand the design based on that summaries
    * Note that sometimes a summary might not be there due to any reason since forgetting to create or even losing it
* For Operations mode:
    * When generating code, please go step by step, make one change at a time
    * If you are unsure about something, ask for clarification.
    * DO NOT MAKE UP FACTS. If you don't know, say "I don't know".
    * NEVER, EVER MAKE assumptions, ALWAYS ask for clarification.
    * Stick strictly to the request, do not go beyond what is asked.
    * Always use the commands in the make file. If they are not there please suggest adding them.

* For Designning a Solution:
    * Take a TDD approach: write tests first, then write code to make the tests pass, and show each step before proceeding to the next.
    * Follow the SOLID principles of software development.
    * Use the best practices of software engineer, balancing for good engineering without over engineering
    * Always proposes a desgin before anything that we can discuss to reach to a agreed implementation

* For Coding:
    * TRY TO KEEP LOGGING STATEMENTS INTO A single LINE
    * Add type hints and maintain them updated
    * Imports ALWAYS goes to the top of the file
    * Start with test that fails and move from ther in TDD fashion
    * use extreme programming paradigm when coding and consider myself as your senior peer/counterpart
    * Ask me to review and approve what you created as your extreme programmer peer
    * In between each step of the implementaiton plan when using TDD, ask me if I want to git commit
    * For commits there is no need for statistics mentioning how many tests were ran or passed
    * ALWAYS go step by step, do not create multiple files at same time, do not create multiple classes at same time
    * NEVER Create a whole solution end to end. Give small baby steps towards the end goal.

* For testing follow the below instructions
    * When creating tests, always run first the ones you just created, and if they pass, then run all the tests.
    * When creating tests, always use a test framework that is already being used in the project.
    * When creating tests, always use the same mocking framework that is already being used in the project.
    * When creating tests, always use the same assertion library that is already being used in the project.
    * When creating tests, always use the same naming conventions that are already being used in the project.
    * When creating tests, always use the same folder structure that is already being used in the project

* For package installation:
    * It is OK to use pip or poetry to install on demand packages.
    * All on-demand packages installed should be added to the dependencies file, being it requirements.txt, project.toml or other

* For After Work:
    * Always create a summary of the work done.
    * Save it as a .md file in summaries sub directory
    * Start the name with a data in the form YYYY-MM-DD-{some proper identifiable name}

