# black-jack
modified version of Blackjack game where a human player interacts with three AI agents (A, B, and C).

1. Basic Overview -
This program gives a solution for a modified version of Blackjack game where a human player
interacts with three AI agents (A, B, and C). The game uses the LangChain framework and
OpenAI's language models to create intelligent agents that can make decisions and deal cards.
The user cannot call the card generator function directly; instead, they must request a crew agent
(A, B, or C) to “deal” the card on their behalf.

2. Game Rules -
The game follows Blackjack rules with some simple unique modifications:
• Each participant (user and AI crew - agents) can hold a maximum of 3 cards
• Cards are integers from 2 to 11 only
• Going over 21 points results in a disqualification
• The game runs for a maximum of 3 rounds
• The highest total under or equal to 21 wins

3. Agent Framework
The game implementation utilizes LangChain's agent framework:
• Decision Making: Each AI agent uses an LLMChain to decide whether to draw or hold
for themselves
• Card Dealing: Agents use a LangChain Agent with a custom tool to generate and deal
cards
• System Messages: Each agent receives strict instructions via system messages to ensure
proper behavior

4. High-Level Architecture -

a. Participants:
• User – Represents the human player. Prompts appear in the command line, asking
whether to “draw (1)”, request “advice (2)”, or “skip (3)”
• AI Crew – Three AI agents (A, B,C)
Each agent maintains its own total, decides whether to “draw” or “hold,” and can deal
cards to the user upon request.

b. Card Generation Tool:
• The local Python function generator() returns a random integer in [2..11].
• A LangChain Tool (draw_tool) wraps this function.
• Only the AI agents (via a strict system message) can invoke draw_tool, ensuring the
user never directly calls it.

c. Gameplay Workflow:
Initialization – The Three AI agents are created, each with:
• A LangChain Agent configuration (to call draw_tool).
• An LLMChain used for deciding its own choices (“draw” or “hold”).

The user’s card list is empty at the start.
Rounds -

User Turn: The user decides an action:
draw: Specifies which agent (A, B, or C) should deal them a card.
advice: Gets a basic suggestion from Agents collectively (example: “draw” or
“hold,” based on a simple threshold).
skip: Signals they do not want more cards.

AI Crew Turns:
Each agent decides, via its LLMChain prompt, if it wants to draw for itself.
If it chooses “draw,” the agent calls the draw_tool, updates its total, and possibly disqualifies if >21.

Ending Conditions -
• Each participant (user + agents) can hold max 3 cards.
• The game ends early if everyone has either disqualified or finished drawing.
• After up to 3 rounds, the game concludes automatically.
Determining the Winner -
• Any participant with a total ≤ 21 is eligible.
• If no one is ≤ 21, no winner is declared.
• Otherwise, the highest total ≤ 21 wins. Ties occur if multiple participants share the
same best total.

d. Agentic Details:
LangChain Configuration
• Tool: draw_tool calls generator(), returning a random integer in [2..11].
• Agents: Each AI agent has a system message instructing it to strictly return only the
integer when dealing a card for the user or to respond with “draw” / “hold” for its
own decisions.
• Regex scanning ensures any extra text from the LLM is filtered out and only a valid
integer is processed.


Minimizing Errors
• Temperature = 0: The AI is guided to follow instructions exactly rather than producing
any “creative” text.
• System Prompt: The prompt strongly states that the final answer can only be an integer if
a new card is drawn.
• Regex: If the AI still includes extra text, we scan for the integer pattern (2..11) and
discard the rest.

5. Running the Game -

To run the Blackjack game, you need to have the necessary libraries and configurations in
place. Below are the steps to get the game up and running:

Step 1: Set up the environment
• Make sure you have Python installed.
• Install the required dependencies, including the langchain openai

Step 2 : OpenAI Key
• Provide your OpenAI credentials via environment variable or directly:
• OPENAI_API_KEY="xxxxxxx"
Step 3:Execution
• Save the script for instance, as blackjack.py
• The game will begin immediately, displaying a welcome message.

Step 4: Gameplay
• Type 1 to draw a card from a specified agent.
• Type 2 for advice to see a suggestion from Agents collectively.
• Type 3 if you want to hold.
• The AI agents automatically take their turns afterward.
• After at most 3 rounds, the final results are printed.

6. Limitations and Future Enhancements -
Round 1: User takes deal though Agent B

Round 2: User takes advice from the agents collectively and then takes the deal through Agent c.

Round 3: User takes the advice from all the agents collectively and then holds/skip.
