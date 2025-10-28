[![Open in Codespaces](https://classroom.github.com/assets/launch-codespace-2972f46106e565e64193e422d61a12cf1da4916b45550586e14ef0a7c637dd04.svg)](https://classroom.github.com/open-in-codespaces?assignment_repo_id=21342349)
# Homework 3
For this project, you will be able to work with a partner. You can select a partner and share your github repository between the two of you. Additionally, you will need to have a design document where you have the specifications of your application. This could either be a text document that lives in your repl.it workspace or you could use another collaborate platform such as Google Docs or a Microsoft Word shared document.

You will be creating a board game that is played using a graphical interface. The design and layout of the game will be left to you and your team.

The game should be able to read from a file to get score, players, and game piece positions. The game status saved in the file should be thought of as a way to save your game and come back to it later. You don't need to continually update the information but you should be able to reconstruct a game based on file.

### Design Document
Create a document that sketches a visual of how your game will look. Where will you display the following:
- Game Name
- Game Spaces
- Player status
- Games pieces on a game space.
- Extra information if needed.

[Sample Design Document](https://docs.google.com/document/d/1xXQPjdLHRItnFXNEhXRUR7GD2Vof4vvSIap0wAtoHWM/edit?usp=sharing)
- Note that the sample example is for a calendar project. The ideas are the same but the code (while helpful) does not directly apply to your current problem.



#### Design Questions
- What are the rules to the game?
  - You don't need to fully implement the game
  - How is it played, is there a dice roll or some other action?
- How are the player pieces visually identified.
- What other elements are in the game?
- What input from the user would you need to make the game go?
  - Do they click, is there text input?

#### Event File
You will need to have a file in the same folder as your BoardGame.py that has a listing of events.
You and your team will need to decide how to store information in this file.
- What is the format of info in the file?
  - Turn: Player 1
  - 3: Player 1
  - 4: Player 2
  - 17: Hotel
  - 20: Troll

- What happens if there are multiple pieces on the same spot?
  - 3: Player 1, Hotel, Troll

#### Problem Deconstruction
What functions will you use in your program?
How will using these functions help to simplify the overall design?
Who is in charge of each function (if working with a partner)?

### ChatGPT Prompt
This is a tricky part of the assignment. ChatGPT is able to write the starter code for a web application using Flask but you need to carefully craft the prompt you supply.

Here is the prompt I used to generate this sample game. Just to be clear, this is a poor example of a game because I have not fully identified the rules. It is a fine sample output even though it is incomplete.

```
Write a flask app that allows hexagon tiles to be added to a game board when the user clicks. This is a 2 player game and the tiles will be laid in alternating order. All of player 1's tiles will be green and all of player 2's tiles will be blue.
```

### Running a Flask App
Flask uses HTML, Java Script, and Python to create web applications. We don't need to know everything about this platform but it allows us to utilize the coding language we have been learning.

In the terminal window you will need to install Flask in your Code Space

```
pip install Flask
```

After that, you can run BoardGame.py and it will create a web server which can be viewed in a browser window.


### Final Submission
Your final work should include:
- Design Document
- BoardGame FLask App
  - Submit a document with link to your github repository.
- Events document
