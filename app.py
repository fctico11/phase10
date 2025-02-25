from flask import Flask, render_template, request, redirect, url_for
from game_logic import Game

app = Flask(__name__)
game = Game()

@app.route("/")
def home():
    return render_template("game.html", game=game)

@app.route("/draw", methods=["POST"])
def draw_card():
    if game.current_turn == "player":
        from_discard = "from_discard" in request.form
        game.draw_card("player", from_discard=from_discard)
    return redirect(url_for("home"))

@app.route("/select_card", methods=["POST"])
def select_card():
    card_index = int(request.form["card_index"])
    game.select_card(card_index)
    return redirect(url_for("home"))

@app.route("/discard", methods=["POST"])
def discard_card():
    if game.current_turn == "player":
        success = game.discard_selected_card()
        if success and not game.skip_turn:
            return redirect(url_for("computer_turn"))
    return redirect(url_for("home"))

@app.route("/computer_turn")
def computer_turn():
    if game.current_turn == "computer":
        game.computer_turn()
    return redirect(url_for("home"))

@app.route("/submit_phase", methods=["POST"])
def submit_phase():
    game.submit_phase()
    return redirect(url_for("home"))

@app.route("/add_to_phase", methods=["GET", "POST"])
def add_to_phase():
    if request.method == "GET":
        card_index = int(request.args.get("card_index"))
    else:
        card_index = int(request.form["card_index"])
    game.add_to_phase_attempt(card_index)
    return redirect(url_for("home"))

@app.route("/remove_from_phase", methods=["GET", "POST"])
def remove_from_phase():
    if request.method == "GET":
        card_index = int(request.args.get("card_index"))
    else:
        card_index = int(request.form["card_index"])
    game.remove_from_phase_attempt(card_index)
    return redirect(url_for("home"))

@app.route("/hit_phase", methods=["POST"])
def hit_phase():
    card_index = int(request.form["card_index"])
    game.hit_existing_phase(card_index)
    return redirect(url_for("home"))

@app.route("/reset_game", methods=["POST"])
def reset_game():
    game.reset_game()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
