import random
from typing import List, Optional
import os
import re
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage
from langchain.chains import LLMChain
from langchain.agents import (
    Tool,
    AgentType,
    initialize_agent,
)

def generator():
    return random.randint(2, 11)

def draw(_query: str):
    status = generator()
    return str(status)

draw_tool = Tool(
    name="draw",
    func=draw,
    description=(
        "When the player selects draw, then use this tool which returns a random integer from 2..11"
    ),
)

CREW_AGENT_MESSAGE = """
You are an AI agent player in a simplified Blackjack-like game.
You can do TWO possible actions:
1) Decide for YOURSELF whether to 'draw' or 'hold' using a single word. 
2) If the user requests you to deal them a card, you must call the 'draw_card' tool
   and in your FINAL answer, return ONLY the integer from 2..11, with no extra text 
   or punctuation.

Constraints:
- Cards are integers in the range [2..11].
- A participant can hold a maximum of 3 cards.
- If a participant's total exceeds 21, they disqualify.
- If you are drawing for YOURSELF, respond with 'draw' or 'hold' only.
- If you are dealing for the USER, you must return only the integer in your final message.
"""

prompt_logic = PromptTemplate(
    input_variables=["crew_name", "running_total"],
    template="""
You are {crew_name}, playing a simplified Blackjack-like game for YOURSELF.
Your total is {running_total}.
Decide whether to take another card or hold.

Respond with exactly one word: "draw" or "hold".
"""
)

def decision_logic(api_key: str, temperature: float = 0.0): #-> LLMChain
    langchain = ChatOpenAI(openai_api_key=api_key, temperature=temperature)
    return LLMChain(llm=langchain, prompt=prompt_logic)

class AI_agent:
    def __init__(self, name: str, key: str):
        self.name = name
        self.cards: List[int] = []
        self.has_stopped = False
        self.decision_chain = decision_logic(api_key=key, temperature=0.0)
        system_msg = SystemMessage(content=CREW_AGENT_MESSAGE)
        llm = OpenAI(openai_api_key=key, temperature=0.0)
        self.agent = initialize_agent(
            tools=[draw_tool],
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            system_message=system_msg.content,
        )

    def running_total(self):
        return sum(self.cards)

    def disqualified(self):
        return self.running_total() > 21

    def can_draw(self):
        return len(self.cards) < 3 and not self.disqualified() and not self.has_stopped

    def decide_logic(self):
        if not self.can_draw():
            return False

        result = self.decision_chain.invoke({
            "crew_name": self.name,
            "running_total": str(self.running_total())
        })
        action = result["text"].strip().lower()
        return (action == "draw")

    def draw_card(self, card_val: int):
        self.cards.append(card_val)

    def stop_draw(self):
        self.has_stopped = True

    def reset(self):
        self.cards.clear()
        self.has_stopped = False

    def user_draw(self) -> Optional[int]:
        user_instruction = "I want to draw a card for myself now. Return only the integer 2..11."
        response = self.agent.invoke({"input": user_instruction})
        raw_output = response.get("output", "") or response.get("text", "")
        raw_output = raw_output.strip()

        match = re.search(r"\b([2-9]|10|11)\b", raw_output)
        if match:
            return int(match.group(1))
        return None

    def agent_deal(self) -> Optional[int]:
        user_instruction = "The user wants a card. Return ONLY the integer in your final answer (2..11)."
        response = self.agent.invoke({"input": user_instruction})
        result = response.get("output", "") or response.get("text", "")
        result = result.strip()

        match = re.search(r"\b([2-9]|10|11)\b", result)
        if match:
            return int(match.group(1))
        return None

class Blackjack:
    def __init__(self, key: str):
        self.crew_agents = [
            AI_agent("A", key),
            AI_agent("B", key),
            AI_agent("C", key),
        ]
        self.user_cards: List[int] = []
        self.user_stopped = False

    def reset_game(self):
        self.user_cards.clear()
        self.user_stopped = False
        for i in self.crew_agents:
            i.reset()

    def user_total(self) -> int:
        return sum(self.user_cards)

    def user_disqualified(self) -> bool:
        return self.user_total() > 21
    
    def user_turn(self):
        while True:
            if self.user_disqualified() or len(self.user_cards) >= 3 or self.user_stopped:
                return

            cmd = input("Your turn! Enter [draw(1), advice(2), skip(3)]: ").strip().lower()
            if cmd == "1":
                agent_name = input("Which agent (A/B/C) do you choose to deal? ").strip()
                agent = self.get_agent_by_name(agent_name)
                if agent is None:
                    print("No such agent. Try again.")
                    continue

                card_value = agent.agent_deal()
                if card_value is None:
                    print(f"{agent.name} did not produce a valid integer card.")
                else:
                    self.user_cards.append(card_value)
                    print(f"You drew a card: {card_value}. Your total is now {self.user_total()}.")
                break

            elif cmd == "2":
                adv = "draw" if (self.user_total() < 17) else "hold"
                print(f"Crew Agents suggests collectively: {adv}")

            elif cmd == "3":
                self.user_stopped = True
                print("You decided to hold.")
                break

            else:
                print("Invalid command. Please try again.")

    def get_agent_by_name(self, name: str):
        for i in self.crew_agents:
            if i.name.lower() == name.lower():
                return i
        return None

    def agent_turn(self, i: AI_agent):
        if not i.can_draw():
            return

        will_draw = i.decide_logic()
        if will_draw:
            card_value = i.user_draw()
            if card_value is None:
                print(f"[{i.name}] did not produce a valid card for themself.")
            else:
                i.draw_card(card_value)
                print(f"[{i.name}] drew {card_value}. Total={i.running_total()}")
                if i.disqualified():
                    print(f"[{i.name}] disqualify!")
                    i.stop_draw()
                elif len(i.cards) >= 3:
                    i.stop_draw()
        else:
            i.stop_draw()
            print(f"[{i.name}] holds (Total={i.running_total()}).")

    def play_rounds(self, max_rounds=3):
        for r in range(1, max_rounds + 1):
            print(f"\n Round {r}")
            
            if not self.user_disqualified() and len(self.user_cards) < 3 and not self.user_stopped:
                self.user_turn()
                if self.user_disqualified():
                    print("You exceeded 21")
                if len(self.user_cards) == 3:
                    print("You have drawn 3 cards")

            for i in self.crew_agents:
                if not i.disqualified() and len(i.cards) < 3 and not i.has_stopped:
                    self.agent_turn(i)

            self.print_totals()

            if self.everyone_done():
                print("Exiting")
                break

        self.announce_winners()

    def everyone_done(self):
        user_done = self.user_disqualified() or (len(self.user_cards) >= 3) or self.user_stopped
        all_agents_done = True
        for i in self.crew_agents:
            if (not i.disqualified()) and (len(i.cards) < 3) and (not i.has_stopped):
                all_agents_done = False
                break
        return user_done and all_agents_done

    def print_totals(self):
        print("\n Running Totals")
        disqualified_user = "(BUST)" if self.user_disqualified() else ""
        print(f"User: {self.user_total()} {disqualified_user}")
        for i in self.crew_agents:
            disqualified_str = "Disqualified" if i.disqualified() else ""
            print(f"{i.name}: {i.running_total()} {disqualified_str}")
        print("----------------------\n")

    def announce_winners(self):
        valid_scores = []
        if self.user_total() <= 21:
            valid_scores.append(("User", self.user_total()))

        for i in self.crew_agents:
            if i.running_total() <= 21:
                valid_scores.append((i.name, i.running_total()))

        if not valid_scores:
            print("\nNo valid winners")
            return

        best_score = max(s for _, s in valid_scores)
        winners = [p for p, sc in valid_scores if sc == best_score]

        print("\nFinal Results ")
        print(f"User: {self.user_total()}{' Disqualified' if self.user_disqualified() else ''}")
        for i in self.crew_agents:
            bstr = "Disqualified" if i.disqualified() else ""
            print(f"{i.name}: {i.running_total()} {bstr}")

        if len(winners) == 1:
            print(f"\nWinner: {winners[0]} with {best_score}")
        else:
            print(f"\nIt's a tie among: {', '.join(winners)} (Score={best_score})")

def start_game():
    try:
        key = os.getenv("OPENAI_API_KEY", "xxxxxxx")
        game = Blackjack(key=key)
        game.reset_game()

        print("Hello, welcome to the Blackjack game")

        game.play_rounds(max_rounds=3)

    except Exception as e:
        print(f"Error: {e}")

start_game()