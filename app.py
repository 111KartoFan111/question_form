from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Подключаемся к базе данных
def get_db_connection():
    conn = sqlite3.connect('polls.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создает таблицы при первом запуске
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poll_id INTEGER,
                    question TEXT NOT NULL,
                    FOREIGN KEY (poll_id) REFERENCES polls (id))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS choices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER,
                    choice TEXT,
                    votes INTEGER DEFAULT 0,
                    FOREIGN KEY (question_id) REFERENCES questions (id))''')
    conn.close()

# Переход на Main
@app.route('/')
def home():
    conn = get_db_connection()
    polls = conn.execute('SELECT * FROM polls').fetchall()
    conn.close()
    return render_template('home.html', polls=polls)

# Переход на страницу голосования
@app.route('/poll/<int:poll_id>', methods=['GET', 'POST'])
def poll(poll_id):
    conn = get_db_connection()
    poll = conn.execute('SELECT * FROM polls WHERE id = ?', (poll_id,)).fetchone()
    questions = conn.execute('SELECT * FROM questions WHERE poll_id = ?', (poll_id,)).fetchall()
    # Получение вариантов ответов
    choices = {}
    for question in questions:
        choices[question['id']] = conn.execute(
            'SELECT * FROM choices WHERE question_id = ?', (question['id'],)
        ).fetchall()
    conn.close()

    if request.method == 'POST':
        for question in questions:
            choice_id = request.form.get(f'choice_{question["id"]}')
            if choice_id:
                conn = get_db_connection()
                conn.execute('UPDATE choices SET votes = votes + 1 WHERE id = ?', (choice_id,))
                conn.commit()
                conn.close()
        return redirect(url_for('results', poll_id=poll_id))

    return render_template('poll.html', poll=poll, questions=questions, choices=choices)


# Переход на страницу результатов
@app.route('/results/<int:poll_id>')
def results(poll_id):
    conn = get_db_connection()
    poll = conn.execute('SELECT * FROM polls WHERE id = ?', (poll_id,)).fetchone()
    questions = conn.execute('SELECT * FROM questions WHERE poll_id = ?', (poll_id,)).fetchall()
    # Получение результатов для каждого вопроса
    choices = {}
    for question in questions:
        choices[question['id']] = conn.execute(
            'SELECT * FROM choices WHERE question_id = ?', (question['id'],)
        ).fetchall()
    conn.close()

    return render_template('results.html', poll=poll, questions=questions, choices=choices)

# Страница для создания нового опроса
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        questions = request.form.getlist('question')
        choices_list = [request.form.getlist(f'choice_{i}') for i in range(len(questions))]

        # Сохранение опроса и вопросов
        conn = get_db_connection()
        conn.execute('INSERT INTO polls (title) VALUES (?)', (title,))
        poll_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        for i, question_text in enumerate(questions):
            if question_text.strip():
                conn.execute('INSERT INTO questions (poll_id, question) VALUES (?, ?)', (poll_id, question_text))
                question_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

                # Сохранение вариантов ответов для каждого вопроса
                for choice in choices_list[i]:
                    if choice.strip():
                        conn.execute('INSERT INTO choices (question_id, choice) VALUES (?, ?)', (question_id, choice))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('create.html')

# Запуск приложения
if __name__ == '__main__':
    init_db()
    app.run(debug=True)