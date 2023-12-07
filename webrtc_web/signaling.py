
from flask import Flask, request, Response
from flask_socketio import SocketIO, emit
import json
from flask_cors import CORS
print("hello world")


app = Flask(__name__)
CORS(app, cors_allowed_origins="*")
socketio = SocketIO(app)

data = {}
users = {}


@app.route('/test')
def test():
    return Response('{"status":"ok"}', status=200, mimetype='application/json')


def broadcast_offer(offer_data):
    print(" offer data", offer_data)
    socketio.emit('getOffer', offer_data)


@app.route('/offer', methods=['POST'])
def offer():
    if request.form["type"] == "offer":
        offer_data = {"id": request.form['id'],
                      "type": request.form['type'], "sdp": request.form['sdp'], "target": request.form['target']}
        data["offer"] = offer_data
        broadcast_offer(offer_data)
        return Response(status=200)
    else:
        return Response(status=400)


def broadcast_answer(answer_data):
    print(" answer data", answer_data)
    socketio.emit('getAnswer', answer_data)


@app.route('/answer', methods=['POST'])
def answer():
    if request.form["type"] == "answer":
        data["answer"] = {"id": request.form['id'],
                          "type": request.form['type'], "sdp": request.form['sdp']}
        broadcast_answer(data["answer"])
        return Response(status=200)
    else:
        return Response(status=400)


@app.route('/get_answer', methods=['GET'])
def get_answer():
    if "answer" in data:
        j = json.dumps(data["answer"])
        del data["answer"]
        return Response(j, status=200, mimetype='application/json')
    else:
        return Response(status=503)


@socketio.on('register')
def on_register(data):
    username = data['username']
    socket_id = request.sid
    users[username] = socket_id
    emit('update_users', list(users.keys()), broadcast=True)
    print(f'User registered: {username} with socket ID: {socket_id}')


@socketio.on('connect')
def on_connect():
    print('User connected:', request.sid)


@socketio.on('disconnect')
def on_disconnect():
    user_to_remove = None
    for user, socket_id in users.items():
        if socket_id == request.sid:
            user_to_remove = user
            break
    if user_to_remove:
        del users[user_to_remove]
        emit('update_users', list(users.keys()), broadcast=True)
    print('User disconnected:', request.sid)


if __name__ == '__main__':
    socketio.run(host="0.0.0.0", port=6969, debug=True, app=app)
