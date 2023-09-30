from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
from keyboard import press
import random
from string import ascii_uppercase


app = Flask(__name__)
app.config['SECRET_KEY'] = "secret"
socketio = SocketIO(app)
timestamp = datetime.now().strftime('%H:%M:%S')
rooms = {}

def generate_unique_code(length) :
    while True :
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms :
            break
    return code

@app.route('/', methods=['GET', 'POST'])
def home() :
    if request.method == 'POST' :
        session.clear()
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False) # ketika button tidak diletakkan False maka akan return None(error) jadi kita return false aja
        create = request.form.get('create', False)
        
        if not name :
            return render_template('home.html', error="please pick a name", code=code, name=name)
        if not code and join != False :
            return render_template('home.html', error="please enter a room code", code=code, name=name)
        
        room = code
        if create != False :
            room = generate_unique_code(4)
            rooms[room] = {'members': 0, "messages":[]}
        elif code not in rooms :
            return render_template('home.html', error='the room doesnt not exist', code=code, name=name)

        session['room'] = room
        session['name'] = name

        return redirect(url_for('room'))
    return render_template('home.html')

@app.route('/room', methods=['POST', 'GET'])
def room() :
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home', error='please_complete_the_form'))
    
    return render_template('room.html', code= room, messages= rooms[room]['messages'],time = datetime.now().strftime('%H:%M:%S'))

@socketio.on('connect')
def connect(auth):
    name = session.get('name')
    room = session.get('room')
    time = datetime.now().strftime('%H:%M:%S')
    if not name or not room :
        return
    if room not in rooms :
        leave_room(room)
    join_room(room)
    send({'name': name,'message': "has entered the room", 'timestamp': time}, to= room)   # Json Message into data
    rooms[room]['members'] += 1
    print(f'{name} has joined {room} at {time}')  

@socketio.on('disconnect')
def disconnect() :
    name = session.get('name')
    room = session.get('room')
    time = datetime.now().strftime('%H:%M:%S')
    leave_room(room)
    if room in rooms :
        rooms[room]['members'] -= 1
        if rooms[room]['members'] <= 0 :
            del rooms[room]
    send({'name': name, 'message' : 'has left the room', 'timestamp':time}, to= room)   # Json Message into data
    print(f'{name} has left {room} at {timestamp}')
    
@socketio.on ('message')  # Event listener
def message(data) :  
    room = session.get('room')
    if room not in rooms :
        return
    content = {
        "name": session.get('name'),
        "message" : data['data'],
        "timestamp" : datetime.now().strftime('%H:%M:%S')
    }
    send(content, to= room) 
    rooms[room]['messages'].append(content)
    print(f'{session.get("name")} said: {data["data"]} at {timestamp}')  # parameters data = {'data': 'wqe'}

if __name__ == "__main__":
    socketio.run(app, debug=True)