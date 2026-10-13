import shutil
from typing import Callable

from . import games
from .accounts import Account
from .config import Config
from .types import GameContext
from .utils import cprint, cinput, clear_screen, display_topbar, get_theme
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button, Input, Static

CASINO_HEADER = """
┌──────────────────────────────────────┐
│   ♦ T E R M I N A L  C A S I N O ♦   │
└──────────────────────────────────────┘
"""

CASINO_HEADER_OPTIONS = {
    "header": CASINO_HEADER,
    "margin": 3,
}
ACCOUNT_STARTING_BALANCE = 100

class CasinoHome(App):

    # Implements the CSS and the homepage where the user can enter name, then a button per game.
    # Clicking on button opens up a game.
    CSS="""
    Screen {
        align: center middle;
    }
    #header {
        width: auto; 
        color: gold; 
        text-style: bold;
        }
    #name-input {
        width: 40; 
        border: tall gold;
        }
    #name-input:focus {
        border: tall gold;
        }
    #welcome {
        width: auto; 
        color: gold; 
        margin-bottom: 1;
        }
    #games {
        layout: grid; 
        grid-size: 2; 
        grid-gutter: 1; width: 60; 
        height: auto;
        }
    #games Button {
        width: 100%;
        }
    """

    # Empty player name for later
    player_name= ""

    def compose(self) -> ComposeResult:
        self.welcome= Static("", id="welcome")
        self.games_box= Container(id="games")
        return [
            # Creates a header
            Static(CASINO_HEADER, id="header"),
            # Creates a welcome message
            self.welcome,
            # The name input area
            Input(placeholder="Enter your name", id="name-input"),
            # And the holder for the buttons
            self.games_box,
        ]

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # When enter is selected in name box
        name= event.value.strip()
        # If there is no name don't proceed
        if not name:
            return

        # Save name and get rid of the input box
        self.player_name= name
        event.input.remove()
        # Welcome message
        self.welcome.update(f"Welcome, {name}! Please choose a game:")
        # Buttons
        for game in ALL_GAMES:
            self.games_box.mount(*[Button(game.title(), name=game)])

    # When a button is pressed, open up the game
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.exit((self.player_name, event.button.name))

ENTER_OR_QUIT_PROMPT = "[E]nter   [Q]uit: "
INVALID_CHOICE_PROMPT = "\nInvalid input. Please try again.\n"
GAME_CHOICE_PROMPT = "Please choose a game to play: "

# To add a new game, just add a handler function to GAME_HANDLERS

GAME_HANDLERS: dict[str, Callable[[GameContext], None]] = {
    "blackjack (U.S.)": games.blackjack.play_blackjack,
    "blackjack (E.U.)": games.blackjack.play_european_blackjack,
    "slots": games.slots.play_slots,
    "slots (Expanded)": games.slots.play_slots_expanded,
    "poker": games.poker.play_poker,
    "roulette": games.roulette.play_roulette,
    "uno": games.uno.play_uno,
    "european roulette": games.roulette.play_european_roulette,
}
ALL_GAMES = list(GAME_HANDLERS.keys())

def term_width() -> int:
    """Safe terminal width fallback."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def prompt_with_refresh(
    render_fn: Callable[[], None],
    prompt: str,
    error_message: str,
    validator: Callable[[str], bool],
    transform: Callable[[str], str] = lambda s: s.strip(),
) -> str:
    """
    Repeatedly render screen, show last error (if any), ask for input and validate.
    On EOF/KeyboardInterrupt return 'q' so caller can decide how to exit.
    """
    last_error = ""
    while True:
        render_fn()
        if last_error:
            cprint(last_error)
        answer = transform(cinput(prompt).strip())
        if validator(answer):
            return answer
        last_error = error_message

def main_menu(ctx: GameContext) -> None:
    """
    Main loop: show welcome, then (if chosen) show game menu, call handler,
    then return to top-level menu. No recursion used.
    """
    account = ctx.account
    while True:
        def render_welcome():
            clear_screen()
            display_topbar(account, **CASINO_HEADER_OPTIONS)
            cprint("")  # spacing

        action = prompt_with_refresh(
            render_fn = render_welcome,
            prompt = ENTER_OR_QUIT_PROMPT.center(term_width()),
            error_message = INVALID_CHOICE_PROMPT,
            validator = lambda x: x.lower() in {"e", "q"},
            transform = lambda s: s.strip().lower(),
        )

        if action == "q":
            clear_screen()
            display_topbar(account, **CASINO_HEADER_OPTIONS)
            cprint("\nGoodbye!\n")
            break  # exit loop -> program ends

        # --- choose game ---
        def render_choose_game():
            clear_screen()
            display_topbar(account, **CASINO_HEADER_OPTIONS)
            cprint("")  # spacing
            width = term_width()
            max_length = max(map(len, ALL_GAMES))
            cprint("┌" + "─" * 30 + "┐")
            cprint("│" + " " * 30 + "│")
            for i, name in enumerate(ALL_GAMES, start=1):
                cprint(
                    f"│{('[{}] {}'.format(i, name.title()) + ' ' * (max_length - len(name))).center(30)}│".center(width)
                )
            cprint("│" + " " * 30 + "│")
            cprint("└" + "─" * 30 + "┘")



        choice = prompt_with_refresh(
            render_fn = render_choose_game,
            prompt = GAME_CHOICE_PROMPT.center(term_width()),
            error_message = INVALID_CHOICE_PROMPT,
            validator = lambda x: x.isdigit() and 1 <= int(x) <= len(ALL_GAMES),
        )

        selected_game = ALL_GAMES[int(choice) - 1]
        handler = GAME_HANDLERS.get(selected_game)
        if handler:
            clear_screen()
            handler(ctx)  # returns to loop after game finishes
        else:
            clear_screen()
            display_topbar(account, **CASINO_HEADER_OPTIONS)
            cprint("\nNo such game!\n")


def main(name: str):

    clear_screen()
    display_topbar(account=None, **CASINO_HEADER_OPTIONS)

    
    name =name
    # theme selection
    clear_screen()
    display_topbar(account=None, **CASINO_HEADER_OPTIONS)
    get_theme()


    account = Account.generate(name, ACCOUNT_STARTING_BALANCE)
    config = Config.default()
    ctx = GameContext(account=account, config=config)
    main_menu(ctx)


if __name__ == "__main__":
    try:
        # Show textual homepage
        result= CasinoHome().run()
        # Player quits without putting anything in, exit
        if result is None:
            raise SystemExit

        # Name and game pair
        name, game= result

        # Sets up what the games need
        account= Account.generate(name, ACCOUNT_STARTING_BALANCE)
        ctx= GameContext(account=account, config=Config.default())
        clear_screen()
        GAME_HANDLERS[game](ctx)
    except (KeyboardInterrupt, EOFError):
        clear_screen()
        display_topbar(account=None, **CASINO_HEADER_OPTIONS)
        cprint("\nGoodbye! (Interrupted)\n")

